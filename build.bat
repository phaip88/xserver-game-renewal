@echo off
echo Compiling Java code...
javac minecraft.java
if %ERRORLEVEL% neq 0 (
    echo Compilation failed!
    pause
    exit /b 1
)

echo Creating manifest file...
echo Main-Class: minecraft > Manifest.txt

echo Creating JAR file...
jar cvmf Manifest.txt server.jar *.class META-INF/
if %ERRORLEVEL% neq 0 (
    echo JAR creation failed!
    pause
    exit /b 1
)

echo Cleaning up...
del Manifest.txt
del *.class
echo Compilation successful! server.jar created.
pause