' tangoya.vbs — Windows 실행 파일 (창 없이 실행)
' 더블클릭하면 명령 프롬프트 창 없이 바로 서버가 시작됩니다.
' Python이 설치되어 있어야 합니다. (https://www.python.org)

Option Explicit

Dim oShell, oFSO, scriptDir, pyPath, batPath

Set oShell = CreateObject("WScript.Shell")
Set oFSO   = CreateObject("Scripting.FileSystemObject")

' 이 .vbs 파일이 있는 폴더를 기준으로 경로 설정
scriptDir = oFSO.GetParentFolderName(WScript.ScriptFullName)

' Python 실행 파일 찾기 (python / python3 모두 시도)
pyPath = ""
On Error Resume Next
pyPath = oShell.Exec("where python").StdOut.ReadLine()
On Error GoTo 0

If pyPath = "" Then
    MsgBox "Python이 설치되어 있지 않습니다." & vbCrLf & vbCrLf & _
           "https://www.python.org 에서 Python 3를 설치한 후" & vbCrLf & _
           "다시 실행해 주세요." & vbCrLf & vbCrLf & _
           "설치 시 'Add Python to PATH' 옵션을 반드시 체크해 주세요.", _
           vbCritical, "tangoya — Python 필요"
    WScript.Quit 1
End If

' 창 없이(0) start_server.py 실행
oShell.Run "python """ & scriptDir & "\start_server.py""", 0, False
