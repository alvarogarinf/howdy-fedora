CLAUDE.md — howdy-fedora
Qué es este proyecto

Repositorio de empaquetado RPM para publicar Howdy (autenticación facial estilo Windows Hello vía PAM) en un COPR para Fedora.

Aquí NO se desarrolla Howdy ni dlib. Este repo solo contiene recetas de construcción (spec files, módulo SELinux, scripts de build/CI). El código fuente se descarga de las releases oficiales upstream mediante Source: en los specs.

Por qué existe
Upstream está parado: último commit en master el 2025-06-22 (release 3.0.0). Hay decenas de PRs abiertos sin revisar. No dependemos de que upstream acepte nada.
El COPR de referencia (principis/howdy y principis/howdy-beta) está abandonado: solo tiene builds para fc43 y fallan en Fedora 44.
Ningún paquete de Fedora 44 proporciona python3dist(dlib), que Howdy necesita.
Los usuarios de Fedora están instalando a mano desde el código fuente (ver issues upstream #1135, #1069, #1038, #1066, #1026).
Objetivo

Que en Fedora 44 (y rawhide) baste con:

bash
sudo dnf copr enable <usuario>/howdy
sudo dnf install howdy

y que Howdy funcione con sudo, pantalla de bloqueo y gestor de inicio de sesión (GNOME/GDM y KDE Plasma/SDDM/plasmalogin) con SELinux en modo enforcing.

Paquetes a producir
python3-dlib: bindings de Python de dlib compilados para el Python del sistema (Fedora 44 → Python 3.14), instalados en el site-packages del sistema, NUNCA en /usr/local. Debe proporcionar python3dist(dlib).
howdy: Howdy 3.0.0. Depende de python3-dlib. Instala pam_howdy.so en la ruta estándar de PAM (%{_libdir}/security/) e incluye los modelos de dlib.
howdy-selinux (subpaquete): módulo SELinux que permita a los dominios confinados del greeter/lock screen (xdm_t) usar la cámara (V4L, incluido map).

Orden de construcción obligatorio: python3-dlib primero, luego howdy.

Problemas conocidos que el empaquetado debe resolver

Estos fallos se han reproducido en hardware real al instalar a mano:

dlib en /usr/local no se encuentra bajo PAM/sudo: con dlib instalado vía sudo pip install, compare.py falla con ModuleNotFoundError: No module named 'dlib' cuando lo lanza PAM desde sudo, aunque root y el usuario lo importen sin problema. Solución: dlib empaquetado en el site-packages del sistema.
meson install no descarga los modelos de dlib: sin ellos, howdy test falla con RuntimeError: Unable to open .../shape_predictor_5_face_landmarks.dat. Los modelos deben ir como Source: adicionales (sin descargas en %post ni durante el build). Modelos: shape_predictor_5_face_landmarks.dat, dlib_face_recognition_resnet_model_v1.dat, mmod_human_face_detector.dat (repo davisking/dlib-models, comprimidos en .bz2).
La pantalla de bloqueo de KDE autentica como el usuario, no como root: los modelos faciales y la configuración deben ser legibles por el proceso de autenticación de Plasma. Por eso, NO aplicar permisos 0600 root-only a los modelos (propuesta del PR upstream #1106) sin comprobar antes que no rompe el desbloqueo en KDE.
SELinux bloquea la cámara en el greeter (denied { map } sobre /dev/video* desde xdm_t). Base para el módulo: PR upstream #1118 e issue #1026 (en reference/).
No sobrescribir archivos PAM del sistema: el paquete NO debe editar /etc/pam.d/* automáticamente. La activación la hace el usuario; documentarla en el README.
Reglas de empaquetado
Seguir las Fedora Packaging Guidelines y las Python Packaging Guidelines (macros pyproject cuando aplique).
Builds sin acceso a red: todo lo que se necesite, como Source:.
Versiones fijadas. Para Howdy, usar el tag de la release 3.0.0 si existe; si no, fijar un commit concreto y documentarlo. Verificar antes de asumir.
Licencias: declarar con identificadores SPDX y usar %license. Verificar la licencia de cada modelo de dlib antes de incluirlo; no suponerla.
Pasar rpmlint sobre specs y RPMs resultantes; explicar cualquier warning que se deje.
Mensajes de changelog claros; incrementar Release en cada cambio.
Flujo de trabajo
bash
# Construir localmente
rpmbuild -bs <spec>                     # generar SRPM (o spectool -g para fuentes)
mock -r fedora-44-x86_64 --rebuild <srpm>
# howdy necesita el RPM de python3-dlib: usar mock --chain o --addrepo con el resultado anterior

# Lint
rpmlint <spec> <rpms>

# Publicar
copr-cli build howdy <srpm>
Restricciones para Claude
No ejecutar nada con sudo salvo mock. No instalar paquetes en el sistema.
No modificar nada fuera de este repositorio. En particular, nunca tocar /etc/pam.d/.
Explicar cada decisión de empaquetado relevante, sobre todo lo que afecte a PAM, SELinux o permisos: es autenticación del sistema y el autor debe revisarlo todo.
Ante una duda sobre guidelines, versiones o licencias, verificar o preguntar; no inventar.
reference/ contiene material de terceros solo como contexto (no se commitea).
Entorno de pruebas del autor
ASUS Zenbook 14, Fedora 44, KDE Plasma con SDDM, SELinux enforcing.
Cámara IR en /dev/v4l/by-path/pci-0000:00:14.0-usb-0:9:1.2-video-index0 (/dev/video2, formato GREY 640x360). Emisor IR funciona sin linux-enable-ir-emitter.
Actualmente tiene una instalación manual en /usr/local que se retirará para probar los paquetes.
Fuera de alcance (por ahora)
Cambios en el código de Howdy salvo parches mínimos imprescindibles para empaquetar (junto al spec de su paquete, <paquete>/*.patch, porque rpmbuild y COPR buscan Source/Patch en el directorio del spec; documentados y con referencia al issue/PR upstream si existe).
Otras distros.
Entrada en los repos oficiales de Fedora (posible objetivo futuro).