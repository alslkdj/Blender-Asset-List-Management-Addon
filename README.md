# 블렌더 애셋리스트 관리 애드온
#### 이 애드온은 블렌더 상에서 제작된 애셋의 정보를 구글시트에 동기화함으로써 아티스트 및 프로그래머 사이의 명확한 애셋리스트 관리를 편리하게 하기 위해 제작되었습니다.

------------------------------------------------------------------------------------------

Python을 이용해 제작되었으며 **gspread**모듈을 통한 구글 스프레드시트 동기화, **uuid**모듈을 통한 개체 간 관리를 하였습니다.

익스포터에서 **bpy.ops.custom.gspreadpush(블렌더 오브젝트, 내보내는 파일명)** 을 호출하여 사용함으로써 애셋의 익스포트 단계에서 자동으로 구글 스프레드시트에 오브젝트 정보가 최신화됩니다.

* 저희 팀의 경우, 블렌더 기본 익스포터 외 다른 익스포터에 결합하여 사용하였기에 저작권 상 예시 코드를 업로드 할 수 없음에 양해 바라겠습니다.
* 팀 프로젝트만을 위한 일회성으로 만들어져 구글 스프레드시트명 등 일정 부분 하드코딩 되어있는 부분이 있음에 양해 부탁드립니다.



<br/><br/><br/><br/><br/>

# Blender Asset List Management Addon
#### It was made for easy management the asset list between Artists and Programmers with upload asset's data on Google Spreadsheet.

------------------------------------------------------------------------------------------

Made by used Python. It can Google Spreadsheet sync by used the **gspread** module and object management by used the **uuid** module.

When call **bpy.ops.custom.gspreadpush(Blender Object, Export FileName)** on exporter, the addon works. Then, the addon upload data on spreadsheet when it works.

* I'm apologizing that I can't show the example code of exporter. Because the exporter using on my project is not mine so I afraid of copyright.
* It was made only for my team project. So I'm sorry that may some variable (ex: google sheet name...) is hard coded. 
