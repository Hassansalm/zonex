import flet as ft
import os
import asyncio
import base64
import sys
import urllib.request

import firebase_admin
from firebase_admin import credentials, storage, firestore

# --- إعدادات البيئة والمسارات ---
if getattr(sys, 'frozen', False):
    bundle_dir = os.path.dirname(sys.executable)
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

FIREBASE_JSON_PATH = os.path.join(bundle_dir, "assets", "firebase_key.json")

# --- تهيئة الـ Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_JSON_PATH)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'hassan-df1ea.firebasestorage.app'
    })

db = firestore.client()

def get_bucket():
    return storage.bucket()

def main(page: ft.Page):
    page.scroll = 'auto'
    page.padding = 10
    page.theme_mode = ft.ThemeMode.LIGHT
    
    
    # حقول تسجيل الدخول
    user_input = ft.TextField(label="username", border_color=ft.Colors.BLUE)
    pass_input = ft.TextField(label="passowrd", password=True, can_reveal_password=True, border_color=ft.Colors.BLUE)

    # متغيرات التطبيق الخاصة برفع الملفات
    current_folder_id = {"id": ""}
    navigation_stack = []
    all_grid_items = []
    rows_data_list = []
    dynamic_rows_container = ft.Column()
    
    main_zone_tf = ft.TextField(
        label='zone num', 
        color=ft.Colors.BLACK, 
        bgcolor="#FFFFFF", 
        expand=True
    )

    # دالة تسجيل الخروج المشتركة
    def logout_action(e):
        user_input.value = ""
        pass_input.value = ""
        page.navigation_bar = None  
        page.go("/login")           
        page.update()

    # دالة إنشاء مكان الصورة مع إمكانية الحذف
    def create_image_control_with_delete(placeholder_text):
        placeholder_content = ft.Column([
            ft.Icon(ft.Icons.ADD_A_PHOTO_OUTLINED, color=ft.Colors.BLUE_GREY_400, size=20),
            ft.Text(placeholder_text, color=ft.Colors.BLUE_GREY_700, size=10, weight="bold"),
            ft.Text("اضغط", color=ft.Colors.GREY_500, size=8)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

        img_container = ft.Container(
            expand=True,
            height=95,
            bgcolor="#f7f9fa",
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=ft.BorderRadius.all(8),
            alignment=ft.Alignment.CENTER,
            content=placeholder_content
        )
        
        img = ft.Image(
            border_radius=ft.BorderRadius.all(8), 
            src="", 
            gapless_playback=True,
            visible=False
        )

        def delete_click(e):
            img.src = ""
            img.src_base64 = ""
            img.visible = False
            img_container.content = placeholder_content
            delete_btn.visible = False
            page.update()

        delete_btn = ft.IconButton(
            icon=ft.Icons.CANCEL,
            icon_color=ft.Colors.RED_500,
            icon_size=18,
            right=-5,
            top=-5,
            visible=False,
            on_click=delete_click
        )

        async def container_tap(e):
            if not img.visible:
                await pick_image(img, delete_btn, img_container)
            else:
                if img.src:
                    show_full_image(img.src)

        wrapped = ft.GestureDetector(
            content=ft.Stack([img_container, delete_btn]),
            on_tap=container_tap,
            expand=True
        )
        return img, delete_btn, wrapped, img_container

    async def pick_image(target_image, delete_btn, parent_container):                     
        files = await ft.FilePicker().pick_files(allow_multiple=False, with_data=True, file_type=ft.FilePickerFileType.IMAGE)
        if files:
            selected = files[0]
            if selected.path:
                target_image.src = selected.path
            elif selected.bytes:
                b64 = base64.b64encode(selected.bytes).decode("utf-8")
                target_image.src = f"data:image/jpeg;base64,{b64}"
            
            target_image.visible = True
            parent_container.content = target_image
            delete_btn.visible = True
            
            parent_container.update()
            delete_btn.update()

    def get_fat_options() -> list[ft.DropdownOption]:
        return [ft.DropdownOption(key=f"fat {i}", text=f"fat {i}") for i in range(1, 49)]

    # دالة إضافة سطر حقول جديد
    def add_new_data_row(e=None):
        fat_dd = ft.Dropdown(
            editable=True,                  
            label='fat num',
            color=ft.Colors.BLACK,
            bgcolor="#FFFFFF",
            elevation=5,
            menu_height=250,
            menu_width=100,
            expand=True,
            options=get_fat_options(),      
        )
        
        img_before_in, del_before_in, wrap_before_in, _ = create_image_control_with_delete("Inside Before")
        img_before_out, del_before_out, wrap_before_out, _ = create_image_control_with_delete("Outside Before")
        img_after_in, del_after_in, wrap_after_in, _ = create_image_control_with_delete("Inside After")
        img_after_out, del_after_out, wrap_after_out, _ = create_image_control_with_delete("Outside After")

        notes_tf = ft.TextField(
            label='Comment', 
            color=ft.Colors.BLACK, 
            bgcolor="#FFFFFF", 
            multiline=True, 
            min_lines=1, 
            max_lines=3,
            expand=True
        )

        def delete_this_row(e):
            if len(rows_data_list) == 1:
                page.overlay.append(ft.SnackBar(ft.Text("⚠️ بطل الواتة حباب", rtl=True, size=16), open=True))
                page.update()
                return
            
            dynamic_rows_container.controls.remove(row_design)
            for item in rows_data_list:
                if item["design"] == row_design:
                    rows_data_list.remove(item)
                    break
            page.update()

        delete_row_btn = ft.IconButton(
            icon=ft.Icons.DELETE_FOREVER_ROUNDED,
            icon_color=ft.Colors.RED_600,
            icon_size=24,
            tooltip="حذف هذا السطر",
            on_click=delete_this_row
        )

        row_design = ft.Container(
            content=ft.Column([
                ft.Divider(height=2, color=ft.Colors.GREY_400),
                ft.Row(controls=[fat_dd, delete_row_btn], spacing=10),
                ft.Row(
                    controls=[wrap_after_in, wrap_after_out, wrap_before_in, wrap_before_out], 
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
                    spacing=5
                ),
                ft.Row(controls=[notes_tf], spacing=10),
            ]),
        )

        rows_data_list.append({
            "fat": fat_dd,  
            "notes": notes_tf,
            "images": [
                (img_after_out, "Outside_After.jpg"), (img_after_in, "Inside_After.jpg"),
                (img_before_out, "Outside_Before.jpg"), (img_before_in, "Inside_Before.jpg")
            ],
            "design": row_design
        })
        
        dynamic_rows_container.controls.append(row_design)
        page.update()

    image_dialog = ft.AlertDialog(content=ft.Image(src=""), actions=[ft.TextButton("إغلاق", on_click=lambda _: close_dialog())])
    def close_dialog():
        image_dialog.open = False
        page.update()
    def show_full_image(img_src):
        image_dialog.content.src = img_src
        image_dialog.open = True
        page.update()
    page.overlay.append(image_dialog)

    upload_progress = ft.ProgressBar(width=400, color="blue", visible=False)
    progress_text = ft.Text("جاري الحفظ... يرجى الانتظار", visible=False)

    async def handle_upload(e):
        clean_zone = main_zone_tf.value.strip()
        if not clean_zone:
            page.overlay.append(ft.SnackBar(ft.Text("❌ يرجى كتابة الـ Zone في الأعلى أولاً", rtl=True), open=True))
            page.update()
            return
        for dataset in rows_data_list:
            if not dataset["fat"].value:
                page.overlay.append(ft.SnackBar(ft.Text("❌ يرجى ملء حقول Zone واختيار/كتابة الـ FAT لجميع الأسطر", rtl=True), open=True))
                page.update()
                return

        upload_progress.visible = True
        progress_text.visible = True
        send_and_save.disabled = True
        page.update()
        await asyncio.sleep(0.1)

        try:
            bucket = get_bucket()
            for dataset in rows_data_list:
                clean_fat = dataset["fat"].value.strip() 
                clean_notes = dataset["notes"].value.strip()

                if clean_notes:
                    notes_remote_path = f"{clean_zone}/{clean_fat}/Notes.txt"
                    notes_blob = bucket.blob(notes_remote_path)
                    notes_blob.upload_from_string(clean_notes, content_type='text/plain; charset=utf-8')

                for img_control, suffix in dataset["images"]:
                    if not img_control.visible or img_control.src == "":
                        continue

                    remote_path = f"{clean_zone}/{clean_fat}/{clean_fat}_{suffix}"
                    blob = bucket.blob(remote_path)
                    
                    progress_text.value = f"جاري رفع الصور ..."
                    page.update()

                    if img_control.src.startswith("data:image"):
                        header, encoded = img_control.src.split(",", 1)
                        data = base64.b64decode(encoded)
                        blob.upload_from_string(data, content_type='image/jpeg')
                    else:
                        blob.upload_from_filename(img_control.src, content_type='image/jpg')

            page.overlay.append(ft.SnackBar(ft.Text("✅ تم حفظ ورفع جميع البيانات بنجاح"), open=True))
            
            rows_data_list.clear()
            dynamic_rows_container.controls.clear()
            main_zone_tf.value = ""
            
            add_new_data_row() 
            page.go("/home")
            page.update()

        except Exception as ex:
            print(f"Firebase Error: {ex}")
            page.overlay.append(ft.SnackBar(ft.Text(f"❌ خطأ أثناء الحفظ: {ex}"), open=True))
        finally:
            upload_progress.visible = False
            progress_text.visible = False
            send_and_save.disabled = False
            page.update()

    send_and_save = ft.Button("Save files", bgcolor=ft.Colors.BLUE_GREY, color=ft.Colors.WHITE,
                              on_click=lambda e: page.run_task(handle_upload, e),
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                              icon=ft.Icons.DRIVE_FOLDER_UPLOAD)

    add_new_data_row()

    # تصفح الملفات
    images_grid = ft.GridView(runs_count=2, max_extent=200, child_aspect_ratio=0.7, spacing=10)
    search_bar = ft.TextField(label="Search of files", prefix_icon=ft.Icons.SEARCH, height=45, expand=True, text_size=14, content_padding=10, on_change=lambda e: filter_search(e.control.value))

    def filter_search(search_value):
        search_term = search_value.lower().strip()
        if not search_term:
            images_grid.controls = list(all_grid_items)
        else:
            filtered_items = []
            for container in all_grid_items:
                content_layout = container.content
                item_text = ""
                if isinstance(content_layout, ft.Stack):
                    item_text = content_layout.controls[0].controls[1].value
                elif isinstance(content_layout, ft.Column):
                    if len(content_layout.controls) > 1 and isinstance(content_layout.controls[1], ft.Text):
                        item_text = content_layout.controls[1].value
                if search_term in item_text.lower():
                    filtered_items.append(container)
            images_grid.controls = filtered_items
        images_grid.update()

    def load_firebase_images(prefix=""):
        images_grid.controls.clear()
        all_grid_items.clear()
        search_bar.value = ""
        page.update()
        current_prefix = prefix if prefix else ""
        try:
            bucket = get_bucket()
            blobs = bucket.list_blobs(prefix=current_prefix, delimiter='/')
            blob_list = list(blobs) 
            
            if blobs.prefixes:
                for folder in blobs.prefixes:
                    folder_name = folder.strip('/').split('/')[-1]
                    item_container = ft.Container(
                        content=ft.Stack([
                            ft.Column([ft.Icon(ft.Icons.FOLDER, size=50, color="#d1e6a3"), ft.Text(folder_name, size=12, weight="bold")], alignment="center", horizontal_alignment="center"),
                            ft.IconButton(ft.Icons.DOWNLOAD_FOR_OFFLINE, icon_color="blue", icon_size=20, right=0, top=0, on_click=lambda e, f=folder: download_folder_to_local(f))
                        ]),
                        on_click=lambda e, f=folder: open_folder(f), padding=10, border_radius=10, bgcolor=ft.Colors.WHITE10
                    )
                    all_grid_items.append(item_container)

            for blob in blob_list:
                if blob.name == current_prefix: continue
                path_quoted = blob.name.replace("/", "%2F")
                file_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{path_quoted}?alt=media"
                file_name = blob.name.split('/')[-1]

                if file_name == "Notes.txt":
                    try:
                        notes_content = blob.download_as_text(encoding='utf-8')
                    except Exception:
                        notes_content = "فشل في قراءة الملاحظة"

                    item_container = ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.NOTE_ALT_ROUNDED, size=40, color=ft.Colors.ORANGE_700),
                            ft.Text("الملاحظة:", size=11, color=ft.Colors.GREY_700, weight="bold", rtl=True),
                            ft.Text(notes_content, size=12, max_lines=4, overflow=ft.TextOverflow.ELLIPSIS, text_align="center", color=ft.Colors.BLACK)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor="#fff3cd", 
                        border_radius=10,
                        padding=10,
                        alignment=ft.Alignment.CENTER
                    )
                    all_grid_items.append(item_container)
                
                elif file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    item_container = ft.Container(
                        content=ft.Column([
                            ft.Image(src=file_url, height=150, width=150, border_radius=10, error_content=ft.Icon(ft.Icons.BROKEN_IMAGE)),
                            ft.Text(file_name, size=10, overflow=ft.TextOverflow.ELLIPSIS)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        on_click=lambda e, url=file_url: show_full_image(url), padding=5
                    )
                    all_grid_items.append(item_container)
            
            images_grid.controls = list(all_grid_items)
            images_grid.update()
        except Exception as ex:
            page.overlay.append(ft.SnackBar(ft.Text(f"خطأ في التحميل: {ex}"), open=True))
            page.update()
        
    def open_folder(folder_id):
        navigation_stack.append(current_folder_id["id"])
        current_folder_id["id"] = folder_id
        load_firebase_images(folder_id)

    def go_back(e=None):
        if navigation_stack:
            prev = navigation_stack.pop()
            current_folder_id["id"] = prev
            load_firebase_images(prev)
        else:
            # إذا كنا في المجلد الرئيسي لصفحة الملفات وضغطنا رجوع، يرجع لصفحة HOME
            page.go("/home")

    def download_folder_to_local(folder_prefix):
        upload_progress.visible = True
        progress_text.visible = True
        page.update()
        try:
            bucket = get_bucket()
            blobs = list(bucket.list_blobs(prefix=folder_prefix))
            valid_blobs = [b for b in blobs if not b.name.endswith("/")]
            if len(valid_blobs) == 0: raise Exception("المجلد فارغ")
            base_path = "/storage/emulated/0/Download" if os.name == 'posix' else os.path.join(os.path.expanduser("~"), "Downloads")
            download_path = os.path.join(base_path, folder_prefix.strip("/"))
            os.makedirs(download_path, exist_ok=True)
            for blob in valid_blobs:
                blob.download_to_filename(os.path.join(download_path, blob.name.split("/")[-1]))
            page.overlay.append(ft.SnackBar(ft.Text(f"✅ تم تحميل المجلد إلى: {download_path}"), open=True))
        except Exception as ex:
            page.overlay.append(ft.SnackBar(ft.Text(f"❌ فشل التحميل: {ex}"), open=True))
        finally:
            upload_progress.visible = False
            progress_text.visible = False
            page.update()

    # --- ميزة معالجة أزرار الهاتف الفعلي (الرجوع) ---
    def handle_back_button(e: ft.KeyboardEvent):
        # عندما يضغط المستخدم زر الرجوع الفعلي بالهاتف، يتم إرسال المفتاح كـ "Escape"
        if e.key == "Escape":
            if page.route == "/files":
                # إذا كان داخل مجلدات في صفحة الملفات يرجع خطوة للخلف، وإلا يرجع للرئيسية
                go_back()
            elif page.route == "/home":
                # إذا كان بالرئيسية وضغط رجوع يوديه لصفحة تسجيل الدخول
                logout_action(None)
            elif page.route == "/login" or page.route == "/":
                # إذا كان في صفحة تسجيل الدخول يغلق التطبيق
                page.window_destroy()

    # ربط حدث كيبورد الهاتف الفعلي بالدالة للتحكم بالرجوع
    page.on_keyboard_event = handle_back_button

    # --- إجراءات تسجيل الدخول ---
    def login_action(e):
        name = user_input.value.strip()
        pwd = pass_input.value.strip()

        if not name or not pwd:
            page.overlay.append(ft.SnackBar(ft.Text("⚠️يرجى ادخال البيانات الصحيحة", rtl=True), open=True))
            page.update()
            return

        try:
            

            emp = db.collection("employees").where("password", "==", pwd).stream()
            for doc in emp:
                if doc.id == name:
                    page.navigation_bar = nav_bar
                    page.go("/home")
                    return
            
            page.overlay.append(ft.SnackBar(ft.Text("❌ البيانات خاطئة", rtl=True), open=True))
            page.update()
        except Exception as ex:
            page.overlay.append(ft.SnackBar(ft.Text(f"خطأ أثناء التحقق: {ex}", rtl=True), open=True))
            page.update()

    # --- إدارة المسارات والتنقل (Routing) ---
    def route_change(e):
        page.controls.clear()
        page.bgcolor="#ffffff"
        
        # 1. مسار تسجيل الدخول
        if page.route == "/login" or page.route == "/":
            page.navigation_bar = None 
            page.appbar = None
            page.floating_action_button = None
            
            page.add(
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    padding=50,
                    expand=True,
                    content=ft.Column([
                        ft.Image(src=f"cloud.gif",width=300,height=300),
                        ft.Text("welcome...", size=26, weight="bold", color=ft.Colors.BLUE_GREY_800,align=ft.Alignment.BOTTOM_LEFT),
                        ft.VerticalDivider(),
                        user_input, 
                        pass_input,
                        ft.VerticalDivider(),
                        ft.Button(
                            "login", 
                            icon=ft.Icons.LOGIN,
                            on_click=login_action,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            width=200,
                            height=45
                        )
                    ],alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)
                )
            )

        # 2. مسار الصفحة الرئيسية
        elif page.route == "/home":
            nav_bar.selected_index = 0
            
            page.appbar = ft.AppBar(
                title=ft.Text("Zonex", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_ACCENT), 
                center_title=True, 
                bgcolor="#fafcff",
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT_ROUNDED, 
                        icon_color=ft.Colors.RED_600, 
                        tooltip="تسجيل الخروج", 
                        on_click=logout_action
                    )
                ]
            )
            
            page.floating_action_button = ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                bgcolor=ft.Colors.BLUE,
                content=ft.Text("ADD", color=ft.Colors.WHITE, weight="bold"),
                width=110,
                on_click=add_new_data_row,
                tooltip="إضافة حقول جديدة"
            )
            page.floating_action_button_location = ft.FloatingActionButtonLocation.MINI_START_FLOAT
            
            page.add(
                ft.SafeArea(
                    content=ft.Column([
                        ft.Row(controls=[ft.Text("Insert the data and add new fields as desired...", size=16)], alignment=ft.MainAxisAlignment.START),
                        ft.Row(controls=[main_zone_tf], alignment=ft.MainAxisAlignment.CENTER),
                        dynamic_rows_container,
                        ft.Row(controls=[send_and_save], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row(controls=[upload_progress], alignment=ft.MainAxisAlignment.CENTER),  
                        ft.Row(controls=[progress_text], alignment=ft.MainAxisAlignment.CENTER),    
                    ], scroll=ft.ScrollMode.AUTO)
                )
            )

        # 3. مسار تصفح واستعراض الملفات
        elif page.route == "/files":
            nav_bar.selected_index = 1
            page.floating_action_button = None 
            
            page.appbar =None
            
            page.add(
                ft.SafeArea(
                    content=ft.Column([
                        ft.Row([
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back),
                            search_bar,
                            ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: load_firebase_images(current_folder_id["id"]))
                        ], alignment="spaceBetween", vertical_alignment="center"),
                        images_grid
                    ], expand=True)
                )
            )
            load_firebase_images(current_folder_id["id"])
            
        page.update()

    def nav_change(e):
        if e.control.selected_index == 0:
            page.go("/home")
        elif e.control.selected_index == 1:
            page.go("/files")

    nav_bar = ft.NavigationBar(
        adaptive=True, bgcolor="#ffffff", selected_index=0, height=70,
        on_change=nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, selected_icon=ft.Icons.HOME_OUTLINED, label="HOME"),
            ft.NavigationBarDestination(icon=ft.Icons.PERM_MEDIA, selected_icon=ft.Icons.PERM_MEDIA_OUTLINED, label="FILES"),
        ]
    )
    
    page.on_route_change = route_change
    
    if page.route == "/":
        page.go("/login")
    else:
        page.go(page.route)

ft.app(target=main, assets_dir='assets')
