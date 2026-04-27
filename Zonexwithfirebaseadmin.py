import flet as ft
import os
import asyncio
import base64
import firebase_admin
from firebase_admin import credentials, storage
from datetime import timedelta

# ================== FIREBASE AUTH ==================
# استبدل 'serviceAccountKey.json' بمسار ملفك، و 'your-app.appspot.com' برابط الـ Bucket الخاص بك
CRED_PATH = "serviceAccountKey.json"
BUCKET_NAME = "your-app-id.appspot.com" # تجده في صفحة Storage في كونسول Firebase

if not firebase_admin._apps:
    cred = credentials.Certificate(CRED_PATH)
    firebase_admin.initialize_app(cred, {
        'storageBucket': BUCKET_NAME
    })

bucket = storage.bucket()

# ================== FUNCTIONS ==================

# في فايربيز لا نحتاج لإنشاء مجلدات يدوياً، فقط نضع المسار في اسم الملف
# مثال: zone1/fat2/image.jpg سيقوم تلقائياً بتمثيله كمجلدات

def main(page: ft.Page):
    page.window.left = 960
    page.window.height = 960
    page.window.top = 10
    page.window.width = 400
    page.scroll = 'auto'
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    ####### متغيرات الحالة #########
    current_path = {"path": ""} # بديل لـ folder_id
    navigation_stack = []

    zone_name = ft.TextField(label='zone num', color=ft.Colors.BLACK, bgcolor="#FFFFFF")
    fat_name = ft.TextField(label='fat num', color=ft.Colors.BLACK, bgcolor="#FFFFFF")

    # تعريف عناصر الصور
    image_after_out = ft.Image(width=200, height=200, border_radius=10, src="https://via.placeholder.com/150")
    image_after_in = ft.Image(width=200, height=200, border_radius=10, src="https://via.placeholder.com/150")
    image_before_out = ft.Image(width=200, height=200, border_radius=10, src="https://via.placeholder.com/150")
    image_before_in = ft.Image(width=200, height=200, border_radius=10, src="https://via.placeholder.com/150")

    # أزرار الاختيار
    select_after_out = ft.Button("قبل للفات من الخارج", on_click=lambda e: page.run_task(pick_image, e, image_after_out), icon=ft.Icons.ADD_PHOTO_ALTERNATE)
    select_after_in = ft.Button("قبل للفات من الداخل", on_click=lambda e: page.run_task(pick_image, e, image_after_in), icon=ft.Icons.ADD_PHOTO_ALTERNATE)
    select_before_out = ft.Button("بعد للفات من الخارج", on_click=lambda e: page.run_task(pick_image, e, image_before_out), icon=ft.Icons.ADD_PHOTO_ALTERNATE)
    select_before_in = ft.Button("بعد للفات من الداخل", on_click=lambda e: page.run_task(pick_image, e, image_before_in), icon=ft.Icons.ADD_PHOTO_ALTERNATE)

    # نافذة العرض
    image_dialog = ft.AlertDialog(content=ft.Image(src=""), actions=[ft.TextButton("إغلاق", on_click=lambda _: close_dialog())])
    def close_dialog(): image_dialog.open = False; page.update()
    def show_full_image(img_src): image_dialog.content.src = img_src; image_dialog.open = True; page.update()
    page.overlay.append(image_dialog)

    async def pick_image(e, target_image):
        file_picker = ft.FilePicker(on_result=None)
        page.overlay.append(file_picker)
        page.update()
        files = await file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)
        if files and files[0].path:
            target_image.src = files[0].path
            target_image.update()

    upload_progress = ft.ProgressBar(width=400, color="blue", visible=False)
    progress_text = ft.Text("جاري الحفظ في Firebase...", visible=False)

    ########## رفع الملفات لـ Firebase #######
    async def handle_upload(e):
        if not zone_name.value or not fat_name.value:
            page.snack_bar = ft.SnackBar(ft.Text("يرجى إدخال رقم zone والـ FAT"))
            page.snack_bar.open = True
            page.update()
            return

        upload_progress.visible = True
        progress_text.visible = True
        send_and_save.disabled = True
        page.update()

        try:
            # المسار في Firebase Storage
            base_path = f"{zone_name.value}/{fat_name.value}/"
            
            images_to_upload = [
                (image_after_out, "Outside_Before"),
                (image_after_in, "Inside_Before"),
                (image_before_out, "Outside_After"),
                (image_before_in, "Inside_After")
            ]

            for img_control, prefix in images_to_upload:
                if img_control.src and not img_control.src.startswith("https://via"):
                    file_name = f"{prefix}_{os.path.basename(img_control.src)}"
                    full_firebase_path = f"{base_path}{file_name}"
                    
                    def upload_task():
                        blob = bucket.blob(full_firebase_path)
                        blob.upload_from_filename(img_control.src)
                        blob.make_public() # لجعل الرابط متاح للعرض
                    
                    await asyncio.to_thread(upload_task)

            page.snack_bar = ft.SnackBar(ft.Text("✅ تم الرفع لـ Firebase بنجاح!"))
            page.snack_bar.open = True
            # تصفير الحقول
            zone_name.value = ""; fat_name.value = ""
            default_img = "https://via.placeholder.com/150"
            for img in [image_after_out, image_after_in, image_before_out, image_before_in]: img.src = default_img

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ خطأ: {ex}"))
            page.snack_bar.open = True
        finally:
            upload_progress.visible = False; progress_text.visible = False; send_and_save.disabled = False
            page.update()

    send_and_save = ft.ElevatedButton("حفظ الملف", on_click=lambda e: page.run_task(handle_upload, e), icon=ft.Icons.CLOUD_UPLOAD)

    ########### عرض الملفات من Firebase ############
    images_grid = ft.GridView(runs_count=2, max_extent=200, spacing=10)

    def load_firebase_files(prefix=""):
        images_grid.controls.clear()
        page.update()
        try:
            # جلب الملفات والمجلدات الوهمية
            blobs = bucket.list_blobs(prefix=prefix, delimiter='/')
            
            # 1. عرض المجلدات
            for folder in blobs.prefixes:
                folder_display_name = folder.replace(prefix, "").strip("/")
                images_grid.controls.append(
                    ft.Container(
                        content=ft.Column([ft.Icon(ft.Icons.FOLDER, size=40, color="#d1e6a3"), ft.Text(folder_display_name, size=12)]),
                        on_click=lambda e, p=folder: open_folder(p),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                        padding=10, border_radius=10, ink=True
                    )
                )

            # 2. عرض الصور
            # نحتاج لإعادة استدعاء القائمة بدون محدد (delimiter) لجلب الملفات داخل المسار الحالي فقط
            blobs_files = bucket.list_blobs(prefix=prefix)
            for blob in blobs_files:
                # التأكد أن الملف في المجلد الحالي وليس في مجلد فرعي عميق
                relative_path = blob.name.replace(prefix, "")
                if "/" not in relative_path and relative_path != "":
                    img_url = blob.public_url
                    images_grid.controls.append(
                        ft.Container(
                            content=ft.Column([ft.Image(src=img_url, height=180, width=180, fit=ft.ImageFit.COVER), ft.Text(relative_path, size=10)]),
                            on_click=lambda e, url=img_url: show_full_image(url),
                            bgcolor=ft.Colors.BLACK12, border_radius=10, padding=5
                        )
                    )
            page.update()
        except Exception as ex:
            print(f"Firebase Load Error: {ex}")

    def open_folder(path):
        navigation_stack.append(current_path["path"])
        current_path["path"] = path
        load_firebase_files(path)

    def go_back(e):
        if navigation_stack:
            prev = navigation_stack.pop()
            current_path["path"] = prev
            load_firebase_files(prev)

    def show_page_of_navBar(index):
        page.controls.clear()
        if index == 0:
            page.appbar = ft.AppBar(title="Firebase Zonex", center_title=True, bgcolor="#3b3d3f")
            page.add(
                ft.Column([
                    ft.Text("ادخل رقم Zone ورقم Fat أولاً", size=14, rtl=True),
                    zone_name, fat_name,
                    ft.Row([select_after_in, select_after_out], alignment="center"),
                    ft.Row([image_after_in, image_after_out], alignment="center"),
                    ft.Row([select_before_in, select_before_out], alignment="center"),
                    ft.Row([image_before_in, image_before_out], alignment="center"),
                    send_and_save, upload_progress, progress_text
                ], horizontal_alignment="center")
            )
        elif index == 1:
            page.appbar = None
            page.add(
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back),
                    ft.Text("Firebase Files", size=20, weight="bold"),
                    ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: load_firebase_files(current_path["path"]))
                ], alignment="spaceBetween"),
                images_grid
            )
            load_firebase_files(current_path["path"])

    nav_bar = ft.NavigationBar(
        selected_index=0,
        on_change=lambda e: show_page_of_navBar(e.control.selected_index),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="HOME"),
            ft.NavigationBarDestination(icon=ft.Icons.STORAGE, label="STORAGE"),
        ]
    )
    page.navigation_bar = nav_bar
    show_page_of_navBar(0)

ft.app(target=main)
