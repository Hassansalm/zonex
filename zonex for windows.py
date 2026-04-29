import flet as ft
import os
import asyncio
import base64
import tempfile
import sys
import shutil

# احذف مكتبات googleapiclient و google-auth
import firebase_admin
from firebase_admin import credentials, storage
# إعدادات Firebase
# بدلاً من الطريقة القديمة، استخدم هذا التحقق:
if getattr(sys, 'frozen', False):
    # مسار التطبيق عند تشغيله كملف EXE
    bundle_dir = os.path.dirname(sys.executable)
else:
    # مسار التطبيق عند تشغيل الكود العادي
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

FIREBASE_JSON_PATH = os.path.join(bundle_dir, "assets", "firebase_key.json")

def get_bucket():
    return storage.bucket()


# ================== FOLDER GET OR CREATE ==================
def get_or_create_folder(service, name, parent_id=None):
    # البحث عن المجلد مع التأكد من وجوده داخل الأب (إن وجد)
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    res = service.files().list(q=query, fields="files(id,name)").execute()
    files = res.get("files", [])

    if files:
        return files[0]["id"]

    # إنشاء المجلد وربطه بالأب إذا تم توفيره
    folder_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    if parent_id:
        folder_metadata["parents"] = [parent_id]

    created = service.files().create(body=folder_metadata, fields="id").execute()
    return created["id"]

    

  ######### mainnn ########  
def main(page:ft.Page) :
    page.window.left=960
    page.window.height=960
    page.window.top=10
    page.window.width=400
    page.scroll='auto'
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK
    
    
    
    
    ####### متغيرات الحالة #########
    current_folder_id = {"id" : ""}
    navigation_stack = []

    zone_name = ft.TextField(label='zone num',color=ft.Colors.BLACK,
                          bgcolor="#FFFFFF",
                          
                          )
    fat_name = ft.TextField(label='fat num',color=ft.Colors.BLACK,
                          bgcolor="#FFFFFF",
                          
                          )
    
    # التعديل: أضفنا e هنا لتجنب خطأ الـ Arguments
    

    select_after_out = ft.Button("قبل للفات من الخارج", bgcolor=ft.Colors.GREY,
                             color=ft.Colors.BLACK,
                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                             on_click=lambda e: page.run_task(pick_image, e, image_after_out),
                             icon=ft.Icons.ADD_PHOTO_ALTERNATE)

    select_after_in = ft.Button("قبل للفات من الداخل", bgcolor=ft.Colors.GREY,
                                color=ft.Colors.BLACK,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                on_click=lambda e: page.run_task(pick_image, e, image_after_in),
                                icon=ft.Icons.ADD_PHOTO_ALTERNATE)

    select_before_out = ft.Button("بعد للفات من الخارج", bgcolor=ft.Colors.GREY,
                                color=ft.Colors.BLACK,
                                on_click=lambda e: page.run_task(pick_image, e, image_before_out),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                icon=ft.Icons.ADD_PHOTO_ALTERNATE)

    select_before_in = ft.Button("بعد للفات من الداخل", bgcolor=ft.Colors.GREY,
                                color=ft.Colors.BLACK,
                                on_click=lambda e: page.run_task(pick_image, e, image_before_in),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                icon=ft.Icons.ADD_PHOTO_ALTERNATE)
        
    image_after_out=ft.Image(width=200 , height=200 ,border_radius=ft.BorderRadius.all(10),src="https://via.placeholder.com/150",gapless_playback=True)
    img_after_out_wrapped = ft.GestureDetector(
        content=image_after_out,
        on_tap=lambda _: show_full_image(image_after_out.src) if image_after_out.src else None
    )
    image_after_in = ft.Image(width=200 , height=200 ,border_radius=ft.BorderRadius.all(10),src="https://via.placeholder.com/150",gapless_playback=True)
    img_after_in_wrapped = ft.GestureDetector(
        content=image_after_in,
        on_tap=lambda _: show_full_image(image_after_in.src) if image_after_in.src else None
    )
    image_before_out = ft.Image(width=200 , height=200  ,border_radius=ft.BorderRadius.all(10),src="https://via.placeholder.com/150",gapless_playback=True)
    img_before_out_wrapped = ft.GestureDetector(
        content=image_before_out,
        on_tap=lambda _: show_full_image(image_before_out.src) if image_before_out.src else None
    )
    image_before_in = ft.Image(width=200 , height=200  ,border_radius=ft.BorderRadius.all(10),src="https://via.placeholder.com/150",gapless_playback=True)
    img_before_in__wrapped = ft.GestureDetector(
        content=image_before_in,
        on_tap=lambda _: show_full_image(image_before_in.src) if image_before_in.src else None
    )

    ######## عرض الصور ######### 
    # نافذة منبثقة لعرض الصورة بحجم كبير
    image_dialog = ft.AlertDialog(
        content=ft.Image(src=""),
        actions=[
            ft.TextButton("إغلاق", on_click=lambda _: close_dialog())
        ],
    )

    def close_dialog():
        image_dialog.open = False
        page.update()

    def show_full_image(img_src):
        image_dialog.content.src = img_src
        image_dialog.open = True
        page.update()

    page.overlay.append(image_dialog)
    
    ####### file picker ########  
    select_image = {"img": None}
    async def pick_image(e, target_image):                     
        select_image["img"] = target_image
        files = await ft.FilePicker().pick_files(
            allow_multiple=False,
            with_data=True,
            file_type=ft.FilePickerFileType.IMAGE,
        )
        if files:
            selected = files[0]
            # على أندرويد path يكون None، نستخدم bytes
            if selected.path:
                select_image["img"].src = selected.path
            elif selected.bytes:
                
                b64 = base64.b64encode(selected.bytes).decode("utf-8")
                select_image["img"].src = f"data:image/jpeg;base64,{b64}"
            select_image["img"].update()
        
    # شريط التحميلي افتراضياً
    upload_progress = ft.ProgressBar(width=400, color="blue", visible=False)
    progress_text = ft.Text("جاري الحفظ... يرجى الانتظار", visible=False)
    ########## هنا الرفع #######
    async def handle_upload(e):
        if not zone_name.value or not fat_name.value:
            page.overlay.append(ft.SnackBar(ft.Text("يرجى إدخال رقم zone والـ FAT", rtl=True), open=True))
            page.update()
            return

        upload_progress.visible = True
        progress_text.visible = True
        send_and_save.disabled = True
        page.update()

        await asyncio.sleep(0.1)

        try:
            bucket = get_bucket()
            clean_zone = zone_name.value.strip()
            clean_fat = fat_name.value.strip()
            
            # الصور التي سيتم رفعها
            images_to_upload = [
                (image_after_out, "Outside_After.jpg"),
                (image_after_in, "Inside_After.jpg"),
                (image_before_out, "Outside_Before.jpg"),
                (image_before_in, "Inside_Before.jpg")
            ]

            for img_control, suffix in images_to_upload:
                if "placeholder.com" in img_control.src:
                    continue

                # تحديد المسار داخل Firebase (Zone / FAT / FileName)
                remote_path = f"{clean_zone}/{clean_fat}/{clean_fat}_{suffix}"
                blob = bucket.blob(remote_path)
                # معالجة الصورة (Base64 أو File Path)
                if img_control.src.startswith("data:image"):
                    header, encoded = img_control.src.split(",", 1)
                    data = base64.b64decode(encoded)
                    
                    blob.upload_from_string(data, content_type='image/jpeg')
                else:
                    
                    blob.upload_from_filename(img_control.src , content_type='image/jpg')

                page.overlay.append(ft.SnackBar(ft.Text("✅ تم الحفظ"), open=True, ))
            
            # تنظيف الحقول
            zone_name.value = ""
            fat_name.value = ""
            default_img = "https://via.placeholder.com/150"
            image_after_out.src = default_img
            image_after_out.src_base64 = "" # استخدام نص فارغ بدل None أحياناً يحل المشكلة في أندرويد
            
            image_after_in.src = default_img
            image_after_in.src_base64 = ""
            
            image_before_out.src = default_img
            image_before_out.src_base64 = ""
            
            image_before_in.src = default_img
            image_before_in.src_base64 = ""
            show_page_of_navBar(0)
            page.update()

        except Exception as ex:
            print(f"Firebase Error: {ex}")
            page.overlay.append(ft.SnackBar(ft.Text(f"❌ خطأ: {ex}"), open=True))
            
        finally:
            upload_progress.visible = False
            progress_text.visible = False
            send_and_save.disabled = False
            page.update()

    send_and_save = ft.Button("حفض الملف", bgcolor=ft.Colors.GREY,
                          color=ft.Colors.BLACK,
                          on_click=lambda e: page.run_task(handle_upload, e),
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                          icon=ft.Icons.DRIVE_FOLDER_UPLOAD)

    
    ########### load file ############
    # عنصر لعرض الصور بشكل شبكي (Grid)
    images_grid =ft.GridView(
        runs_count=2,
        max_extent=200,
        child_aspect_ratio=0.7,
        spacing=10,
        
    )
    def load_firebase_images(prefix=""):
        # تنظيف الشبكة وإظهار مؤشر تحميل (اختياري)
        images_grid.controls.clear()
        page.update()
        
        # التأكد من أن الـ prefix نصي وليس None
        current_prefix = prefix if prefix else ""
        
        try:
            bucket = get_bucket()
            # جلب الملفات
            blobs = bucket.list_blobs(prefix=current_prefix, delimiter='/')
            
            # ملاحظة: يجب استهلاك الـ iterator أولاً لجلب الـ prefixes
            blob_list = list(blobs) 
            
            # 1. عرض المجلدات
            if blobs.prefixes:
                for folder in blobs.prefixes:
                    folder_name = folder.strip('/').split('/')[-1]
                    images_grid.controls.append(
                        ft.Container(
                            content=ft.Stack([ # استخدام Stack لوضع زر التحميل فوق المجلد
                                ft.Column([
                                    ft.Icon(ft.Icons.FOLDER, size=50, color="#d1e6a3"),
                                    ft.Text(folder_name, size=12, weight="bold")
                                ], alignment="center", horizontal_alignment="center"),
                                
                                # زر التحميل في الزاوية
                                ft.IconButton(
                                    icon=ft.Icons.DOWNLOAD_FOR_OFFLINE,
                                    icon_color="blue",
                                    icon_size=20,
                                    right=0,
                                    top=0,
                                    tooltip="تحميل المجلد بالكامل",
                                    on_click=lambda e, f=folder: download_folder_to_local(f)
                                )
                            ]),
                            on_click=lambda e, f=folder: open_folder(f),
                            padding=10, border_radius=10, bgcolor=ft.Colors.WHITE10
                        ) 
                        )

            
            # 2. عرض الصور
            for blob in blob_list:
                if blob.name == current_prefix:
                    continue
                
                # الرابط المباشر للصور في Firebase Storage
                # نقوم بعمل encode لاسم الملف يدوياً ليقبله المتصفح/التطبيق
                path_quoted = blob.name.replace("/", "%2F")
                img_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{path_quoted}?alt=media"
                
                images_grid.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Image(
                                src=img_url, 
                                height=150, 
                                width=150, 
                                border_radius=10, 
                                
                                # إضافة مؤشر تحميل في حال كانت الصورة ثقيلة
                                error_content=ft.Icon(ft.Icons.BROKEN_IMAGE) 
                            ),
                            ft.Text(blob.name.split('/')[-1], size=10, overflow=ft.TextOverflow.ELLIPSIS)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        on_click=lambda e, url=img_url: show_full_image(url),
                        padding=5
                    )
                )
            
            # تحديث الشبكة بعد إضافة كل شيء
            images_grid.update()
            
        except Exception as ex:
            print(f"Error loading images: {ex}")
            page.overlay.append(ft.SnackBar(ft.Text(f"خطأ في التحميل: {ex}"), open=True))
            page.update()
        
    def open_folder(folder_id):
        navigation_stack.append(current_folder_id["id"])
        current_folder_id["id"] = folder_id
        load_firebase_images(folder_id)

    def go_back(e):
        if navigation_stack:
            prev = navigation_stack.pop()
            current_folder_id["id"] = prev
            load_firebase_images(prev)
    
    ###### حفض الملفات ########
    def download_folder_to_local(folder_prefix):
        upload_progress.visible = True
        progress_text.visible = True
        upload_progress.value = 0
        progress_text.value = "جاري تجهيز الملفات..."
        page.update()

        try:
            bucket = get_bucket()
            blobs = list(bucket.list_blobs(prefix=folder_prefix))
            valid_blobs = [b for b in blobs if not b.name.endswith("/")]
            total_files = len(valid_blobs)

            if total_files == 0:
                raise Exception("المجلد فارغ او غير موجود")
                
            # --- التعديل هنا لضمان المسار الصحيح على أندرويد ---
            if os.name == 'posix':  # أندرويد
                # هذا هو المسار العام لمجلد التحميلات في أغلب هواتف أندرويد
                base_path = "/storage/emulated/0/Download"
            else:  # ويندوز
                base_path = os.path.join(os.path.expanduser("~"), "Downloads")
            
            download_path = os.path.join(base_path, folder_prefix.strip("/"))

            # إنشاء المجلد محلياً
            if not os.path.exists(download_path):
                os.makedirs(download_path, exist_ok=True)
            
            download_count = 0
            for blob in valid_blobs:
                file_name = blob.name.split("/")[-1]
                local_file_path = os.path.join(download_path, file_name)

                progress_text.value = f"جاري التحميل: {file_name}"
                page.update()
                
                # تحميل الملف
                blob.download_to_filename(local_file_path)
                download_count += 1
                upload_progress.value = download_count / total_files
                page.update()

            page.overlay.append(ft.SnackBar(ft.Text(f"✅ تم تحميل المجلد إلى: {download_path}"), open=True))

        except Exception as ex:
            # إذا فشل بسبب الصلاحيات، سنعرض رسالة توضح ذلك
            error_msg = f"❌ فشل التحميل: {ex}"
            if "Permission denied" in str(ex):
                error_msg = "❌ خطأ: يرجى منح صلاحية الوصول للملفات من إعدادات التطبيق"
            page.overlay.append(ft.SnackBar(ft.Text(error_msg), open=True))
            
        finally:
            upload_progress.visible = False
            progress_text.visible = False
            page.update()

        
    
    
    
    def show_page_of_navBar(index):
        page.vertical_alignment="center"
        page.horizontal_alignment="center"
        
        page.controls.clear()
     
        

        if index == 0:
            page.appbar=ft.AppBar(
                    title="Zonex",
                    center_title=True,
                    bgcolor="#3b3d3f",
                    title_text_style=ft.TextStyle(
                        size= 24,
                        weight=ft.FontWeight.BOLD,
                        color="#00ffff",
                        
                    )
                    
                )
            page.add(
                ft.Row(controls=[ft.Text("ادخل رقم Zone ورقم Fat اولا",size=14)],alignment=ft.MainAxisAlignment.START,rtl=True),
                ft.Column(controls=[zone_name, fat_name],alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(controls=[select_after_in, select_after_out],alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(controls=[image_after_in, image_after_out],alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(controls=[select_before_in, select_before_out],alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(controls=[image_before_in, image_before_out],alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(controls=[send_and_save], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(controls=[upload_progress], alignment=ft.MainAxisAlignment.CENTER),  # ← جديد
                ft.Row(controls=[progress_text], alignment=ft.MainAxisAlignment.CENTER),    # ← جديد
            )

        elif index == 1:
            page.appbar = None
            page.add(
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back),
                    ft.Text("files", size=30, weight="bold"),
                    ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: load_firebase_images(current_folder_id["id"]))
                ], alignment="spaceBetween"),
                images_grid
            )
            load_firebase_images(current_folder_id["id"])
        

    
    
    nav_bar =ft.NavigationBar(
        adaptive=True,
        animate_offset=300,
        bgcolor="#3b3d3f",
        selected_index=0,
        height=70,
        on_change=lambda e: show_page_of_navBar(e.control.selected_index) ,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.HOME,
                selected_icon=ft.Icons.HOME_OUTLINED ,
                label="HOME"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.PERM_MEDIA,
                selected_icon=ft.Icons.PERM_MEDIA_OUTLINED ,
                label="FILES"
                

            ),
        ]
    )
    page.navigation_bar =nav_bar
    show_page_of_navBar(0)
    
ft.app(target=main, assets_dir='assets')
