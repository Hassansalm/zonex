
import flet as ft
import os
import pickle
import asyncio
import base64


from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = "token.pickle"
CREDENTIALS_FILE = "credentials.json"

BASE_DIR = os.path.dirname(__file__)
TOKEN_FILE = os.path.join(BASE_DIR, "token.pickle")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")

# ================== GOOGLE AUTH ==================
def get_drive_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as t:
            creds = pickle.load(t)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as t:
            pickle.dump(creds, t)

    return build("drive", "v3", credentials=creds)

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
    current_folder_id = {"id" : None}
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
        
    image_after_out=ft.Image(width=200 , height=200 ,border_radius=ft.BorderRadius.all(10),src="https://via.placeholder.com/150")
    img_after_out_wrapped = ft.GestureDetector(
        content=image_after_out,
        on_tap=lambda _: show_full_image(image_after_out.src) if image_after_out.src else None
    )
    image_after_in = ft.Image(width=200 , height=200 ,border_radius=ft.BorderRadius.all(10),src="https://via.placeholder.com/150")
    img_after_out_wrapped = ft.GestureDetector(
        content=image_after_in,
        on_tap=lambda _: show_full_image(image_after_out.src) if image_after_out.src else None
    )
    image_before_out = ft.Image(width=200 , height=200  ,border_radius=ft.BorderRadius.all(10),src="https://via.placeholder.com/150")
    img_after_out_wrapped = ft.GestureDetector(
        content=image_before_out,
        on_tap=lambda _: show_full_image(image_after_out.src) if image_after_out.src else None
    )
    image_before_in = ft.Image(width=200 , height=200  ,border_radius=ft.BorderRadius.all(10),src="https://via.placeholder.com/150")
    img_after_out_wrapped = ft.GestureDetector(
        content=image_before_in,
        on_tap=lambda _: show_full_image(image_after_out.src) if image_after_out.src else None
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
        
    # شريط التحميل - مخفي افتراضياً
    upload_progress = ft.ProgressBar(width=400, color="blue", visible=False)
    progress_text = ft.Text("جاري الحفظ... يرجى الانتظار", visible=False)
    ########## هنا الرفع #######
    async def handle_upload(e):
        
        if not zone_name.value or not fat_name.value:
            page.show_dialog(ft.SnackBar(ft.Text("يرجى إدخال رقم zone والـ FAT",rtl=True)))
            
            page.update()
            return

        upload_progress.visible = True
        progress_text.visible = True
        send_and_save.disabled = True
        page.update()

        try:
            service = await asyncio.to_thread(get_drive_service)
            zone_folder_id = await asyncio.to_thread(get_or_create_folder, service, zone_name.value)
            fat_folder_id = await asyncio.to_thread(get_or_create_folder, service, fat_name.value, zone_folder_id)

            images_to_upload = [
                (image_after_out, "Outside_Before"),
                (image_after_in, "Inside_Before"),
                (image_before_out, "Outside_After"),
                (image_before_in, "Inside_After")
            ]

            for img_control, prefix in images_to_upload:
                if img_control.src and not img_control.src.startswith("https://via"):
                    file_name = f"{prefix}_{os.path.basename(img_control.src)}"
                    
                    def upload_file(img_src=img_control.src, fname=file_name):
                        media = MediaFileUpload(img_src)
                        file_metadata = {"name": fname, "parents": [fat_folder_id]}
                        uploaded = service.files().create(body=file_metadata, media_body=media).execute()
                        service.permissions().create(
                            fileId=uploaded["id"],
                            body={"role": "reader", "type": "anyone"}
                        ).execute()
                    
                    await asyncio.to_thread(upload_file)
            page.show_dialog(ft.SnackBar(ft.Text("✅ تم حفظ جميع الصور بنجاح!"), duration=3000))
            
            zone_name.value = ""
            fat_name.value = ""
            default_img = "https://via.placeholder.com/150"
            image_after_out.src = default_img
            image_after_in.src = default_img
            image_before_out.src = default_img
            image_before_in.src = default_img

        except Exception as ex:
            print(f"Upload Error: {ex}")
            page.show_dialog(ft.SnackBar(ft.Text(f"❌ حدث خطأ: {ex}")))
            
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
    def load_drive_images(folder_id=None):
    # التحقق من أن المستخدم أدخل بيانات البحث
        images_grid.controls.clear()
        page.update()
        try:          

            service = get_drive_service()         
            # 2. جلب الملفات من المجلد
            query = f"'{folder_id or 'root'}' in parents and trashed=false"
            results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
            files = results.get('files', [])

           
            for f in files:
                if f["mimeType"] == "application/vnd.google-apps.folder" :
                    folder_id =f["id"]
                    # الرابط المباشر للمعاينة                        
                    images_grid.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.TASK , size=40 , color="#d1e6a3"),
                                ft.Text(f['name'], size=12, weight="bold", overflow=ft.TextOverflow.ELLIPSIS)
                            ],alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            on_click=lambda e, fid=f["id"]: open_folder(fid),
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                            padding=10, border_radius=10,
                            ink=True
                        )
                    )
                else:
                    img_url = f"https://drive.google.com/thumbnail?id={f['id']}&sz=w1000"
                    images_grid.controls.append(
                        ft.Container(
                            content=ft.Column([ft.Image(src=img_url, height=180,width=180, border_radius=5), 
                                            ft.Container(ft.Text(f["name"], size=10, no_wrap=True,color=ft.Colors.WHITE))]),
                            padding=5, bgcolor=ft.Colors.BLACK12, border_radius=10,
                            on_click=lambda e, url=img_url: show_full_image(url),
                            margin=10,
                            alignment=ft.Alignment.CENTER
                        )
                    )
            page.update()
            #page.snack_bar = SnackBar(Text("تم التحديث!"))
            #page.update()
        except Exception as ex:
            print(f"Error: {ex}")
        
    def open_folder(folder_id):
        navigation_stack.append(current_folder_id["id"])
        current_folder_id["id"] = folder_id
        load_drive_images(folder_id)

    def go_back(e):
        if navigation_stack:
            prev = navigation_stack.pop()
            current_folder_id["id"] = prev
            load_drive_images(prev)

        
    
    
    
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
                    ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: load_drive_images(current_folder_id["id"]))
                ], alignment="spaceBetween"),
                images_grid
            )
            load_drive_images(current_folder_id["id"])
        

    
    
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
