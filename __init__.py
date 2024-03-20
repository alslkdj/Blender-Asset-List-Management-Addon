bl_info = {
    "name": "BlenderAddon_for_Project",
    "description": "있으면 좋을만한 것들?",
    "author": "백승태",
    "version": (0,2),
    "blender": (4,0,1),
    "location": "View3D > NPanel",
    "warning": "",
    "categoty": "Development"
}

import bpy
import blf #블렌더 텍스트 쓰는 모듈
import gpu #GPU 모듈
from gpu_extras.batch import batch_for_shader #보다 하이레벨 GPU 모듈
import bpy_extras #블렌더 기타 모듈, 예: 2D -> 3D 전환 등
import os
from subprocess import check_call #pip 실행용
from datetime import datetime
from uuid import uuid4 #uuid 랜덤 생성


#gspread 임포트 가능여부 확인 및 실패시 설치
try:
    import gspread
    print("gspread 임포트 성공.")
except ImportError:
    import sys
    exe_path = sys.executable

    print("gspread 임포트 실패.")
    check_call([exe_path, "-m", "pip", "install", "gspread"])
    print("gspread pip 설치.")

worksheet = None

# %APPDATA%\gspread 폴더 감지 및 service_account.json 파일 복사
def service_account_copy() :
    import shutil
    def worksheet_setting():
        global worksheet
        gc = gspread.service_account() # 구글 어카운트 가져오기
        worksheet = gc.open("Art_Resources").get_worksheet(0) # 시트 열기

    appdata_path = os.getenv("APPDATA")
    gspread_path = os.path.join(appdata_path, "gspread")
    if not os.path.exists(gspread_path):
        os.makedirs(gspread_path)
    
    json_file_path = os.path.join(gspread_path, "service_account.json")

    if not os.path.exists(json_file_path):
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        source_json_path = os.path.join(current_script_dir, "service_account.json")

        if os.path.exists(source_json_path):
            shutil.copy(source_json_path, json_file_path)
            worksheet_setting()
            print("service_account.json 파일이 %APPDATA%\gspread 경로로 복사되었습니다.")
        else:
            print("현재 애드온 내에 service_account.json 파일이 없습니다.")
    else:
        worksheet_setting()
        print("%APPDATA%\gspread 경로에 이미 service_account.json 파일이 존재합니다.")

#카테고리 드로우 여부
CategoryDraw_handler = None

# 머티리얼 구해서 목록 문자열로 할당
def getMaterial (obj):
    material_name = []

    if len(obj.material_slots) >= 1 :
        have_material = False
        for slot in obj.material_slots :
            if slot.material is not None:
                have_material = True
                break
        if have_material :
            for slot in obj.material_slots:
                if slot.material is not None:
                    material_name.append(str(slot.material.name))
        else : material_name.append(" ─ ")
    else : material_name.append(" ─ ")

    return material_name

# 텍스쳐 구해서 목록 문자열로 할당 / Panel에 label로 각 머티리얼마다 출력
def getTexture (obj, Panel):
    texture_name = []

    if len(obj.material_slots) >= 1:
        have_material = False
        for slot in obj.material_slots: 
            if slot.material is not None:
                have_material = True
                break
        if have_material:
            for slot in obj.material_slots:
                if slot.material is not None and slot.material.use_nodes: # 머티리얼이 있으며 노드를 사용할 때
                    have_texture = False
                    for node in slot.material.node_tree.nodes: # 노드를 순회하며
                        if node.bl_idname == "ShaderNodeTexImage": # 텍스쳐 이미지 존재 여부부터 파악
                            have_texture = True
                            break
                            
                    if have_texture: # 텍스쳐 이미지가 있을 때 list에 append 시작
                        texlist = []
                        for node in slot.material.node_tree.nodes:
                            if node.bl_idname == "ShaderNodeTexImage":
                                texlist.append (node.image.name)
                        texture_name.append(", ".join(texlist))
                        #패널에 출력용
                        if (Panel is not None) : Panel.label (text=str(str(slot.material.name) + " : [ " + ", ".join(texlist) + " ]"), icon= "MATERIAL")
                    else: 
                        texture_name.append ("─")
                        #패널에 출력용
                        if (Panel is not None) : Panel.label (text=str(str(slot.material.name) + " : [ ─ ]"), icon= "MATERIAL")
            return texture_name

        else: 
            texture_name.append(" ─ ")
            #패널에 출력용
            if (Panel is not None) : Panel.label (text=" ─ ", icon= "MATERIAL")
            else : return texture_name
    else: 
        texture_name.append(" ─ ")
        #패널에 출력용
        if (Panel is not None) : Panel.label (text=" ─ ", icon= "MATERIAL")
        else : return texture_name


#Append 및 Clean-Up
class DataManager_Panel(bpy.types.Panel) :
    bl_label = "Blender Data Manager"
    bl_idname = "Project_PT_DataManager_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Project'

    def draw(self, context):
        layout = self.layout

        SA_box = layout.box()
        #SA_box.label(text="폴더 내 모든 .blend 파일을 현재 파일에 Append.")
        SA_box.prop(context.scene, "my_filepath")
        layout.operator("custom.simpleappend")

        #SC_box = layout.box()
        #SC_box.label(text="부모 없는 데이터 클린업")
        layout.operator("custom.simpleclean")
               

    bpy.types.Scene.my_filepath = bpy.props.StringProperty (
        name= "폴더 경로",
        default= "폴더 경로 지정하기",
        description= "Append할 폴더 경로",
        subtype= 'DIR_PATH'
    )

    
#메쉬 이름 변경
class SimpleName_Panel(bpy.types.Panel):
    bl_label = "Simple Name"
    bl_idname = "Project_PT_SimpleName_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Project'    

    def draw (self, context) :
        layout = self.layout

        SN_box = layout.box()
        selected_objects = bpy.context.selected_objects
        if not selected_objects:
            SN_box.label(text="선택된 오브젝트가 없습니다.")
            return
        elif len(selected_objects) == 1:
            selected_object = selected_objects[0]

            SN_box.prop(selected_object, "name", text="오브젝트명", icon= 'OBJECT_DATA')
            SN_box.prop(selected_object.data, "name", text="메쉬명", icon= 'MESH_DATA')
        elif len(selected_objects) >= 2:
            SN_box.label(text= "여러 오브젝트를 선택중입니다.")
        SN_box.operator('custom.simplename')

#시트 관리 최상위 패널
class ObjectManage_Panel (bpy.types.Panel):
    bl_label = "Object Manage"
    bl_idname = "Project_PT_ObjectManage_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Project"

    def draw(self, context):
        layout = self.layout

        
        
#오브젝트 카테고리 어트리뷰트 관리
class SimpleCategories_Panel (bpy.types.Panel) :
    bl_label = "Simple Categories"
    bl_idname = "Project_PT_SimpleCategories_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Project"
    bl_parent_id = "Project_PT_ObjectManage_Panel"

    def draw(self, context) :
        layout = self.layout

        layout.prop(context.scene, "CategoryDraw")
        layout.prop(context.scene, 'Category_List')
        layout.operator('custom.selectbycategory')
        
        SC_box = layout.box()
        selected_objects = context.selected_objects   
        if not selected_objects:
            SC_box.label(text="선택된 오브젝트가 없습니다.")
            return
        elif len(selected_objects) == 1:
            if "Category" in selected_objects[0]:
                obj = selected_objects[0]
                SC_box.label(text= obj["Category"] + " → " + context.scene.Category_List, icon='BOOKMARKS')
            elif "Category" not in selected_objects[0]:
                SC_box.label(text="선택된 오브젝트에 카테고리가 없습니다.")
        elif len(selected_objects) > 1:
            SC_box.label(text= "여러 오브젝트를 선택중입니다.")
        SC_box.operator('custom.setcategory')

    def my_callback(self, context):
        global CategoryDraw_handler
        global Global_CategoryDraw
        Global_CategoryDraw = bpy.context.scene.CategoryDraw

        if bpy.context.scene.CategoryDraw:
            CategoryDraw_handler = bpy.types.SpaceView3D.draw_handler_add(Draw_Category, (None, None), 'WINDOW', 'POST_PIXEL')
            #print("핸들러 Add")
        else :
            bpy.types.SpaceView3D.draw_handler_remove(CategoryDraw_handler, 'WINDOW')
            CategoryDraw_handler = None
            #print("핸들러 Remove")
    
    bpy.types.Scene.CategoryDraw = bpy.props.BoolProperty(
        name= "카테고리 보이기",
        description= "오브젝트에 카테고리 오버레이 UI 드로우 여부",
        default= False,
        update= my_callback
    )
    
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  카테고리 항목들  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    bpy.types.Scene.Category_List = bpy.props.EnumProperty(
        name="카테고리",
        description="카테고리를 선택해주세요.",
        items=[("캐릭터", "캐릭터", "캐릭터입니다"),
                ("캐릭터/무기", "캐릭터/무기", "캐릭터가 사용하는 무기입니다"),
                ("몬스터", "몬스터", "몬스터입니다"),
                ("몬스터/무기", "몬스터/무기", "몬스터가 사용하는 무기입니다"),
                ("배경", "배경", "배경입니다"),
                ("배경/1스테이지", "배경/1스테이지", "배경 중 1스테이지입니다"),
                ("배경/2스테이지", "배경/2스테이지", "배경 중 2스테이지입니다"),
                ("이펙트", "이펙트", "이펙트입니다")],
        default= "배경"
    )
    


#구글 스프레드 시트 연동
class Gspread_Panel (bpy.types.Panel):
    bl_label = "Gspread"
    bl_idname = "Project_PT_Gspread_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Project'
    bl_parent_id = "Project_PT_ObjectManage_Panel"

    def draw (self, context) :                
        layout = self.layout
        
        Gs_box = layout.box()
        
        selected_object = context.selected_objects
        if not selected_object :
            Gs_box.label(text= "선택된 오브젝트가 없습니다.")

        elif len(selected_object) == 1:        
            obj = selected_object[0]

            #UUID 출력
            if 'UUID' not in obj.data:
                Gs_box.label(text="오브젝트에 UUID가 없습니다.")
            else:
                Gs_box.label(text="UUID : " + obj.data['UUID'])
            
            # 카테고리 출력 부분
            if "Category" not in obj :
                Gs_box.label(text=" ─ ", icon="BOOKMARKS")
            elif "Category" in obj:
                Gs_box.label(text=obj["Category"], icon="BOOKMARKS")
            
            # 오브젝트명 출력 부분 (오브젝트가 있으니까 선택된거겠지??)
            Gs_box.label(text=obj.name, icon="OBJECT_DATA")
            
            # 메쉬명 출력 부분 (메쉬가 없을리가 없으니까 그냥함)
            Gs_box.label(text=obj.data.name, icon= "MESH_DATA")

            #머티리얼 + 텍스쳐명 출력
            getTexture(obj, Gs_box)  

            #비고 출력
            if "Note" not in obj:
                Gs_box.label(text="오브젝트에 비고 프로퍼티가 없습니다.")
                Gs_box.operator('custom.notesetting')
            else: 
                Gs_box.prop(obj, '["Note"]', text="비고")
                     
        # 여러 오브젝트 선택 시 출력            
        elif len(selected_object) > 1 :
            Gs_box.label(text= "여러 오브젝트를 선택중입니다.")
            #Gs_box.operator ('custom.gspreadpush')
    
        layout.prop(context.scene, "is_update_gspread")
        layout.operator('custom.gspreadopen')
        layout.operator('custom.gspreaddelete')

            

    

#------------------------------------------------------------------------------------------
#-----------------------------------------Panel--------------------------------------------
#------------------------------------------------------------------------------------------

#폴더 내의 모든 .blend 파일을 현재 파일에 Append
class SimpleAppend(bpy.types.Operator):
    bl_label = "Simple Append"
    bl_idname = "custom.simpleappend"
    bl_description = "폴더 내에 있는 모든 .blend 파일 현재 파일에 Append"

    def invoke (self, context, event):
        if not context.scene.my_filepath : 
            self.report({'ERROR'}, "폴더 경로가 설정되지 않았습니다.")
            return {'CANCELLED'}
        return self.execute(context) 

    def execute(self, context):
        directory = bpy.context.scene.my_filepath
        
        if not os.path.isdir(directory) :
            self.report({'ERROR'}, "잘못된 경로입니다.")
            return {'CANCELLED'}
        
        for filename in os.listdir(directory):
            if filename.endswith(".blend"):
                filepath = os.path.join(directory, filename)
            with bpy.data.libraries.load(filepath) as (data_from, data_to):
                data_to.objects = data_from.objects
            for obj in data_to.objects:
                if obj is not None :
                    context.collection.objects.link(obj)
        for library in bpy.data.libraries:
            bpy.data.libraries.remove(library)

        self.report({'INFO'}, "불러오기 완료.")
        return {'FINISHED'}

#Orphan Data를 Clean-Up
class SimpleClean (bpy.types.Operator):
    bl_label = "Simple Clean"
    bl_idname = "custom.simpleclean"
    bl_description = "현재 파일에 있는 모든 Orphan Data를 삭제"
    
    def execute(self, context):
        bpy.ops.outliner.orphans_purge()
        self.report({'INFO'}, "클린업 완료.")
        return {'FINISHED'}

#메쉬명 및 오브젝트명을 확인하고 메쉬명을 오브젝트명과 동일하게 변경
class SimpleName (bpy.types.Operator):
    bl_label = "오브젝트명 -> 메쉬명 변경"
    bl_idname = "custom.simplename"
    bl_description = "현재 선택한 오브젝트의 메쉬명을 오브젝트명으로 변경"

    def invoke(self, context, event):
        selected_objects = bpy.context.selected_objects
        if len(selected_objects) == 0 :
            self.report({'ERROR'}, "선택된 오브젝트가 없습니다!")
            return {'CANCELLED'}
        elif len(selected_objects) != 0 :
            return self.execute(selected_objects)


    def execute(self, selected_objects):
        for obj in selected_objects:
            if obj.type == 'MESH' or obj.type == 'CURVE' :
                obj.data.name = obj.name
                
        self.report({'INFO'}, "이름 변경 완료.")
        return {'FINISHED'}
    
#카테고리 설정
class SetCategory (bpy.types.Operator) :
    bl_label = "카테고리 설정"
    bl_idname = "custom.setcategory"
    bl_description = "현재 선택한 오브젝트의 카테고리를 상기 설정한 카테고리로 변경 혹은 추가"

    def execute (self, context):
        selected_objects = bpy.context.selected_objects

        for obj in selected_objects:
            obj["Category"] = context.scene.Category_List

        self.report({'INFO'}, "카테고리 설정: "  + context.scene.Category_List)
        return {'FINISHED'}

#카테고리에 따라 선택
class SelectByCategory (bpy.types.Operator):
    bl_label = "카테고리에 있는 오브젝트 선택"
    bl_idname = "custom.selectbycategory"
    bl_description = "상기 선택한 카테고리에 속한 오브젝트를 모두 선택"

    def execute (self, context):
        for obj in context.visible_objects:
            if "Category" in obj and obj["Category"] == bpy.context.scene.Category_List :
                print(obj)
                obj.select_set(True)
        self.report({'INFO'}, bpy.context.scene.Category_List + " 선택")
        return {'FINISHED'}

#비고 프로퍼티 생성
class NoteSetting (bpy.types.Operator):
    bl_label = "비고 프로퍼티 추가"
    bl_idname = "custom.notesetting"
    bl_description = "비고를 작성할 수 있는 커스텀 프로퍼티를 추가합니다"

    def execute (self, context):
        selected_objects = context.selected_objects
        for obj in selected_objects:
            obj["Note"] = ""
        return{"FINISHED"}

#구글 스프레드 시트에 푸쉬
class GspreadPush (bpy.types.Operator):
    bl_label = "구글 시트에 업로드"
    bl_idname = "custom.gspreadpush"
    bl_description = "구글 스프레드 시트에 현재 선택한 오브젝트의 정보를 기입합니다.\n최초 업로드 시 고유한 열을 부여받게 됩니다"

    obj_prop : bpy.props.StringProperty(default="") 
    filename_prop : bpy.props.StringProperty(default=" ─ ") 
    
    def execute (self, context):
        obj = bpy.data.objects.get(self.obj_prop)

        # 빈 셀을 검출
        def find_empty_cell ():
            first_column = worksheet.col_values(1)
            empty_cell = 2

            for i, cell_value in enumerate(first_column):
                if cell_value == '' :
                    empty_cell = int(i) + 1
                    break
                empty_cell =int(i) + 2 #순서대로 올바르게 있으면 빈칸이 카운트가 안돼서 +2해준거임
            return empty_cell
        
        # UUID 없으면 할당, 중복 시 재설정
        def setUUID (obj) :
            if 'UUID' not in obj.data:
                obj.data['UUID'] = str(uuid4())
            else:
                all_objs = bpy.data.objects #모든 오브젝트 가져오기
                all_objs = [other for other in all_objs if other.data is not obj.data] #현재 선택된 오브젝트와 동일한 오브젝트 거르기
                all_objs = [other for other in all_objs if 'UUID' in other.data] #UUID 보유 오브젝트 거르기

                for other in all_objs:
                    if obj.data['UUID'] == other.data['UUID']:
                        obj.data['UUID'] = str(uuid4())

        #UUID 값 시트에서 찾기. 있으면 그 열에 할당, 없으면 빈 열에 
        def findInSheet (obj) :
            row = find_empty_cell()
            
            if 'UUID' in obj.data:
                first_column = worksheet.col_values(9) #UUID 위치
                for i, cell_value in enumerate(first_column):
                    if cell_value == obj.data['UUID']:
                        row = i + 1
                        break
            
            return row

        # 시트에 데이터 푸쉬
        def pushData (obj, filename) :
            setUUID(obj) #UUID 테스트

            row_to_insert = findInSheet(obj)

            if "Category" in obj :
                category = obj['Category']
            else :
                category = " ─ "

            obj_name = obj.name

            mesh_name = obj.data.name

            mat_str = "=SUBSTITUTE(" + '"' + "    ".join(getMaterial(obj)) + '"' + ', "    ", CHAR(10))'

            tex_str = "=SUBSTITUTE(" + '"' + "    ".join(getTexture(obj, None)) + '"' + ', "    ", CHAR(10))'

            if "Note" in obj:
                note_str = obj['Note']
            else: 
                note_str = ""

            updatetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            uuid_str = obj.data['UUID']

            insert_data = [category, filename, obj_name, mesh_name, mat_str, tex_str, note_str, updatetime_str, uuid_str]
            
            cell_to_insert = "A" + str(row_to_insert) # 값 넣기 시작할 셀 정보
            worksheet.update(cell_to_insert, [insert_data], raw=False)
        
            cell_range = str(row_to_insert) + ":" + str(row_to_insert)
            worksheet.format(cell_range, {
                "backgroundColor": {
                    "red": 1.0,
                    "green": 1.0,
                    "blue": 0.0 
                }
            })

        if context.scene.is_update_gspread :
            pushData(obj, self.filename_prop)
        return {'FINISHED'}

# 구글 스프레드시트 열기    
class GspreadOpen (bpy.types.Operator):
    bl_label = "구글 시트 열기"
    bl_idname = "custom.gspreadopen"
    bl_description = "구글 스프레드 시트 열기"  

    def execute (self, context): 
        bpy.ops.wm.url_open(url='https://docs.google.com/spreadsheets/d/1Ad8JZWyBGmNH8620K70G8xyOFj0rZ1J4t8ZATQjHDO4/edit?usp=sharing')
        return {'FINISHED'}
    
# 시트 정보 지우기 (UUID 찾아서 해당 항목 아예 지우기)
class GspreadDelete (bpy.types.Operator):
    bl_label = "선택한 오브젝트 정보 시트에서 지우기"
    bl_idname = "custom.gspreaddelete"
    bl_description = "이 오브젝트의 UUID와 일치하는 시트 상에 있는 행을 삭제합니다."

    def execute (self, context):
        row_list = []

        for obj in bpy.context.selected_objects:
            if 'UUID' in obj.data:
                first_column = worksheet.col_values(9) #UUID 위치
                for i, cell_value in enumerate(first_column):
                    if cell_value == obj.data['UUID']:
                        row_list.append(i+1)
                        print (row_list) #행 리스트에 다 일단 저장해서 일괄 처리
                                   
        if row_list is not None:
            row_list.sort(reverse=True) #저장된 리스트를 역순으로 순회해서 상위 항목 삭제되며 인덱스 꼬이는걸 방지
            for row in row_list:
                worksheet.delete_row(row)

        return {'FINISHED'}

#------------------------------------------------------------------------------------------
#-----------------------------------------Operator-----------------------------------------
#------------------------------------------------------------------------------------------



#카테고리 드로우 핸들러
def Draw_Category(self, context) :
    font_id = 0 #폰트 초기화

    region = bpy.context.region
    rv3d = bpy.context.region_data

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.uniform_float("color", (0,0,0,1))
    for obj in bpy.context.visible_objects:
        coord = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, obj.location)

        if "Category" in obj:
            text = obj['Category']
            text_space = 5
            blf.size(font_id, 24)#글자 사이즈 먼저 정하고
            text_width, text_height = blf.dimensions(font_id, text)#정해진 글자 사이즈에 맞춰 크기 산출

            vertices = (
                (coord.x - text_space, coord.y - text_space), #왼쪽 아래 0 
                (coord.x + text_width + text_space, coord.y - text_space), #오른쪽 아래 1
                (coord.x - text_space, coord.y + text_height + text_space), #왼쪽 위 2
                (coord.x + text_width + text_space, coord.y + text_height + text_space) #오른쪽 위 3
            )

            indices = (
                (0, 1, 2), (2, 1, 3)
            )

            batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
            batch.draw(shader)

            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, coord.x, coord.y, 0)
            blf.draw(font_id, text)




#새 파일 로드할때마다 카테고리 핸들러 지워주기 (안지우면 겹침...)
def load_handler(dummy) :
    #print("되는중!!!!!!!")

    global CategoryDraw_handler

    if CategoryDraw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(CategoryDraw_handler, 'WINDOW')
        CategoryDraw_handler = None

#애드온 로드 시 실행
def register () :
    service_account_copy()
    bpy.app.handlers.load_pre.append(bpy.app.handlers.persistent(load_handler))

    bpy.utils.register_class(DataManager_Panel)
    bpy.utils.register_class(SimpleName_Panel)
    bpy.utils.register_class(ObjectManage_Panel)
    bpy.utils.register_class(SimpleCategories_Panel)
    bpy.utils.register_class(Gspread_Panel)

    bpy.utils.register_class(SimpleAppend)
    bpy.utils.register_class(SimpleClean)
    bpy.utils.register_class(SimpleName)
    bpy.utils.register_class(SetCategory)
    bpy.utils.register_class(SelectByCategory)
    bpy.utils.register_class(NoteSetting)
    bpy.utils.register_class(GspreadPush)
    bpy.utils.register_class(GspreadOpen)
    bpy.utils.register_class(GspreadDelete)


    bpy.types.Scene.is_update_gspread = bpy.props.BoolProperty (
        name= "fbx 익스포트 시 업데이트 여부",
        default= False,
        description= "fbx 익스포트시 시트에 정보를 업데이트할지 여부입니다."
    )


#애드온 언로드 시 실행
def unregister () :
    bpy.app.handlers.load_pre.remove(load_handler)

    bpy.utils.unregister_class(DataManager_Panel)
    bpy.utils.unregister_class(SimpleName_Panel)
    bpy.utils.unregister_class(ObjectManage_Panel)
    bpy.utils.unregister_class(SimpleCategories_Panel)
    bpy.utils.unregister_class(Gspread_Panel)

    bpy.utils.unregister_class(SimpleAppend)
    bpy.utils.unregister_class(SimpleClean)
    bpy.utils.unregister_class(SimpleName)
    bpy.utils.unregister_class(SetCategory)  
    bpy.utils.unregister_class(SelectByCategory)  
    bpy.utils.unregister_class(NoteSetting)
    bpy.utils.unregister_class(GspreadPush)
    bpy.utils.unregister_class(GspreadOpen)
    bpy.utils.unregister_class(GspreadDelete)

    if "CategoryDraw" in bpy.context.scene :
        bpy.context.scene.CategoryDraw = False

    del bpy.types.Scene.is_update_gspread
        

if __name__ == "__main__":
    register()