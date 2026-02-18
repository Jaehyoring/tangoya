' tangoya (単語屋) — Windows 실행기
' 더블클릭으로 실행하면 콘솔 창 없이 브라우저가 열립니다.

Dim sh, proj, python, cmd, ret

Set sh = CreateObject("WScript.Shell")

' 이 파일이 있는 폴더 = 프로젝트 루트
proj = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' Python 경로 확인
On Error Resume Next
ret = sh.Run("cmd /c where pythonw > """ & proj & "py_path.tmp"" 2>nul", 0, True)
On Error GoTo 0

' py_path.tmp 읽기
Dim fs, f, pyPath
Set fs = CreateObject("Scripting.FileSystemObject")
pyPath = ""
If fs.FileExists(proj & "py_path.tmp") Then
    Set f = fs.OpenTextFile(proj & "py_path.tmp", 1)
    If Not f.AtEndOfStream Then pyPath = Trim(f.ReadLine())
    f.Close
    fs.DeleteFile proj & "py_path.tmp"
End If

' pythonw가 없으면 python으로 fallback
If pyPath = "" Then
    ret = sh.Run("cmd /c where python > """ & proj & "py_path.tmp"" 2>nul", 0, True)
    If fs.FileExists(proj & "py_path.tmp") Then
        Set f = fs.OpenTextFile(proj & "py_path.tmp", 1)
        If Not f.AtEndOfStream Then pyPath = Trim(f.ReadLine())
        f.Close
        fs.DeleteFile proj & "py_path.tmp"
    End If
End If

If pyPath = "" Then
    MsgBox "Python이 설치되어 있지 않습니다." & vbCrLf & _
           "https://www.python.org 에서 Python 3.6 이상을 설치해주세요.", _
           vbCritical, "tangoya — 오류"
    WScript.Quit 1
End If

' 이미 포트 8000에서 실행 중인지 확인
ret = sh.Run("cmd /c netstat -ano | findstr :8000 | findstr LISTENING > """ & proj & "port.tmp"" 2>nul", 0, True)
Dim portUsed
portUsed = False
If fs.FileExists(proj & "port.tmp") Then
    Set f = fs.OpenTextFile(proj & "port.tmp", 1)
    If Not f.AtEndOfStream Then portUsed = True
    f.Close
    fs.DeleteFile proj & "port.tmp"
End If

If portUsed Then
    ' 이미 실행 중 → 브라우저만 열기
    sh.Run "http://localhost:8000/tangoya.html"
    WScript.Quit 0
End If

' 콘솔 창 없이 서버 실행 (WindowStyle = 0: 숨김)
cmd = """" & pyPath & """ """ & proj & "dist\start_server.py"""
sh.Run cmd, 0, False

