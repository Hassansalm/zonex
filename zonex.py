from flet import *
import os
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = "token.pickle"
CREDENTIALS_FILE = "credentials.json"

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
def main(page:Page) :
    page.window.left=960
    page.window.height=960
    page.window.top=10
    page.window.width=400
    page.scroll='auto'
    page.padding = 20
    page.theme_mode = ThemeMode.DARK
    
    ####### متغيرات الحالة #########
    current_folder_id = {"id" : None}
    navigation_stack = []

    zone_name = TextField(label='zone num',color=colors.BLACK,
                          bgcolor="#FFFFFF",
                          helper_text='ex: zone 60..',
                          )
    fat_name = TextField(label='fat num',color=colors.BLACK,
                          bgcolor="#FFFFFF",
                          helper_text='ex: fat 29..',
                          )
    
    select_after_out =ElevatedButton("قبل للفات من الخارج" , bgcolor=colors.GREY ,
                                     color=colors.BLACK,
                                     style=ButtonStyle(shape=RoundedRectangleBorder(radius=10)),
                                      on_click=lambda e:pick_image(image_after_out),
                                       icon=icons.ADD_PHOTO_ALTERNATE )
    select_after_in = ElevatedButton ("قبل للفات من الداخل" , bgcolor=colors.GREY ,
                                      color=colors.BLACK ,
                                      style=ButtonStyle(shape=RoundedRectangleBorder(radius=10)),
                                      on_click= lambda e: pick_image(image_after_in),
                                      icon=icons.ADD_PHOTO_ALTERNATE)
    select_before_out = ElevatedButton ("بعد للفات من الخارج" , bgcolor=colors.GREY ,
                                        color=colors.BLACK ,
                                        on_click= lambda e: pick_image(image_before_out),
                                        style=ButtonStyle(shape=RoundedRectangleBorder(radius=10)),
                                        icon=icons.ADD_PHOTO_ALTERNATE)
    select_before_in = ElevatedButton ("بعد للفات من الداخل " , bgcolor=colors.GREY ,
                                       color=colors.BLACK ,
                                       on_click= lambda e:pick_image(image_before_in),
                                       style=ButtonStyle(shape=RoundedRectangleBorder(radius=10)),
                                       icon=icons.ADD_PHOTO_ALTERNATE)
    
    image_after_out=Image(width=200 , height=200 ,fit=ImageFit.COVER ,border_radius=border_radius.all(10),src="https://via.placeholder.com/150")
    img_after_out_wrapped = GestureDetector(
        content=image_after_out,
        on_tap=lambda _: show_full_image(image_after_out.src) if image_after_out.src else None
    )
    image_after_in = Image(width=200 , height=200 ,fit=ImageFit.COVER,border_radius=border_radius.all(10),src="https://via.placeholder.com/150")
    img_after_out_wrapped = GestureDetector(
        content=image_after_in,
        on_tap=lambda _: show_full_image(image_after_out.src) if image_after_out.src else None
    )
    image_before_out = Image(width=200 , height=200 ,fit=ImageFit.COVER ,border_radius=border_radius.all(10),src="https://via.placeholder.com/150")
    img_after_out_wrapped = GestureDetector(
        content=image_before_out,
        on_tap=lambda _: show_full_image(image_after_out.src) if image_after_out.src else None
    )
    image_before_in = Image(width=200 , height=200 ,fit=ImageFit.COVER ,border_radius=border_radius.all(10),src="https://via.placeholder.com/150")
    img_after_out_wrapped = GestureDetector(
        content=image_before_in,
        on_tap=lambda _: show_full_image(image_after_out.src) if image_after_out.src else None
    )

    ######## عرض الصور ######### 
    # نافذة منبثقة لعرض الصورة بحجم كبير
    image_dialog = AlertDialog(
        content=Image(src="", fit=ImageFit.CONTAIN),
        actions=[
            TextButton("إغلاق", on_click=lambda _: close_dialog())
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
    select_image ={"img":None}
    def pick_file_result(e:FilePickerResultEvent):
        if e.files:
            path = e.files[0].path
            select_image["img"].src= path
            page.update()
    file_picker =FilePicker(on_result=pick_file_result)
    page.overlay.append(file_picker)

    ########## button action ##########
    def pick_image(target_image):
        select_image["img"]=target_image
        file_picker.pick_files(allow_multiple=False)

    

    page.update()
        ########## هنا الرفع #######
    # شريط التحميل - مخفي افتراضياً
    upload_progress = ProgressBar(width=400, color="blue", visible=False)
    progress_text = Text("جاري الرفع... يرجى الانتظار", visible=False)
    ########## هنا الرفع #######
    def handle_upload(e):
        if not zone_name.value or not fat_name.value:
            page.snack_bar = SnackBar(Text("يرجى إدخال رقم zone والـ FAT"))
            page.snack_bar.open = True
            page.update()
            return
        upload_progress.visible = True
        progress_text.visible = True
        send_and_save.disabled = True
        page.update()

        try:
            service = get_drive_service()
            zone_folder_id = get_or_create_folder(service, zone_name.value)
            fat_folder_id = get_or_create_folder(service, fat_name.value, parent_id=zone_folder_id)

            images_to_upload = [
                (image_after_out, "Outside_Before"),
                (image_after_in, "Inside_Before"),
                (image_before_out, "Outside_After"),
                (image_before_in, "Inside_After")
            ]

            for img_control, prefix in images_to_upload:
                # نتحقق أن الصورة ليست الرابط الافتراضي قبل الرفع
                if img_control.src and not img_control.src.startswith("https://via"):
                    file_name = f"{prefix}_{os.path.basename(img_control.src)}"
                    media = MediaFileUpload(img_control.src)
                    file_metadata = {
                        "name": file_name, 
                        "parents": [fat_folder_id]
                    }
                    uploaded_file = service.files().create(body=file_metadata, media_body=media).execute()
                    
                    # جعل الملف متاح للجميع (اختياري حسب حاجتك)
                    service.permissions().create(
                        fileId=uploaded_file["id"],
                        body={"role": "reader", "type": "anyone"}
                    ).execute()
            
            # إظهار رسالة النجاح
            page.snack_bar = SnackBar(Text("تم رفع جميع الصور بنجاح!"))
            page.snack_bar.open = True
            
            # تفريغ الواجهة
            zone_name.value = ""
            fat_name.value = ""
            default_img = "https://via.placeholder.com/150"
            image_after_out.src = default_img
            image_after_in.src = default_img
            image_before_out.src = default_img
            image_before_in.src = default_img
            
            page.update()

        except Exception as ex:
            print(f"Upload Error: {ex}")
            page.snack_bar = SnackBar(Text(f"حدث خطأ أثناء الرفع: {ex}"))
            page.snack_bar.open = True
            page.update()
        finally:
        # 2. إخفاء الشريط وإعادة تفعيل الزر في كل الأحوال
            upload_progress.visible = False
            progress_text.visible = False
            send_and_save.disabled = False
            page.update()

    send_and_save = ElevatedButton("حفض الملف" , bgcolor=colors.GREY ,
                                     color=colors.BLACK,
                                     on_click=handle_upload,
                                     style=ButtonStyle(shape=RoundedRectangleBorder(radius=10)),
                                     icon=icons.DRIVE_FOLDER_UPLOAD )
    
    ########### load file ############
    # عنصر لعرض الصور بشكل شبكي (Grid)
    images_grid = GridView(
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
                        Container(
                            content=Column([
                                Icon(icons.TASK , size=40 , color="#d1e6a3"),
                                Text(f['name'], size=12, weight="bold", overflow=TextOverflow.ELLIPSIS)
                            ],alignment=MainAxisAlignment.CENTER,
                            horizontal_alignment=CrossAxisAlignment.CENTER
                            ),
                            on_click=lambda e, fid=f["id"]: open_folder(fid),
                            bgcolor=colors.with_opacity(0.1, colors.WHITE),
                            padding=10, border_radius=10,
                            ink=True
                        )
                    )
                else:
                    img_url = f"https://drive.google.com/thumbnail?id={f['id']}&sz=w1000"
                    images_grid.controls.append(
                        Container(
                            content=Column([Image(src=img_url, height=180,width=180,fit=ImageFit.COVER, border_radius=5), 
                                            Container(Text(f["name"], size=10, no_wrap=True,color=colors.WHITE))]),
                            padding=5, bgcolor=colors.BLACK12, border_radius=10,
                            on_click=lambda e, url=img_url: show_full_image(url),
                            margin=10,
                            alignment=alignment.center 
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
            page.add(
                Column(
                    controls=[
                        zone_name,fat_name
                    ]
                ),
                Row(
                    controls=[
                        select_after_in,select_after_out                     
                    ]
                ),
                Row(
                    controls=[
                        image_after_in,image_after_out
                    ]
                ),
                Row(
                    controls=[
                        select_before_in,select_before_out
                    ]
                ),
                Row(
                    controls=[
                        image_before_in,image_before_out
                    ]
                ),
                Row(
                    controls=[
                        send_and_save
                    ],alignment=MainAxisAlignment.CENTER
                )
            )

        elif index == 1:
            page.add(
                Row([
                    IconButton(icons.ARROW_BACK, on_click=go_back),
                    Text("files", size=30, weight="bold"),
                    IconButton(icons.REFRESH, on_click=lambda _: load_drive_images(current_folder_id["id"]))
                ], alignment="spaceBetween"),
                images_grid
            )
            load_drive_images(current_folder_id["id"])
        

    
    
    nav_bar =NavigationBar(
        adaptive=True,
        animate_offset=300,
        bgcolor="#3b3d3f",
        selected_index=0,
        height=70,
        on_change=lambda e: show_page_of_navBar(e.control.selected_index) ,
        destinations=[
            NavigationBarDestination(
                icon=icons.HOME,
                selected_icon=icons.HOME_OUTLINED ,
                label="HOME"
            ),
            NavigationBarDestination(
                icon=icons.PERM_MEDIA,
                selected_icon=icons.PERM_MEDIA_OUTLINED ,
                label="FILES"
                

            ),
        ]
    )
    page.navigation_bar =nav_bar
    show_page_of_navBar(0)
    
app (target=main,assets_dir='assets')

ما اريدك تغير الكود فقط رتبليا ع اصدار فليت 0.84.0
