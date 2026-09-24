# Upstream never tagged 3.0.0; this is the "Release 3.0.0" merge commit on master
%global commit          d3ab99382f88f043d15f15c1450ab69433892a1c
%global shortcommit     %(c=%{commit}; echo ${c:0:7})
%global models_commit   fd81b6308a6a73d4ce08859eb2f4b628a21e27a2
%global models_url      https://github.com/davisking/dlib-models/raw/%{models_commit}
%global selinuxtype     targeted

Name:           howdy
Version:        3.0.0
Release:        6%{?dist}
Summary:        Windows Hello style facial authentication for Linux

# howdy: MIT
# howdy/src/recorders/v4l2.py: GPL-2.0-or-later OR BSD-3-Clause
# dlib models (howdy-data): CC0-1.0
License:        MIT AND (GPL-2.0-or-later OR BSD-3-Clause)
URL:            https://github.com/boltgolt/howdy
Source0:        %{url}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:        howdy.te
Source2:        README.fedora
Source10:       %{models_url}/shape_predictor_5_face_landmarks.dat.bz2
Source11:       %{models_url}/dlib_face_recognition_resnet_model_v1.dat.bz2
Source12:       %{models_url}/mmod_human_face_detector.dat.bz2
Source13:       %{models_url}/LICENSE#/dlib-models-LICENSE

# SourceFileLoader.load_module() was removed in Python 3.15 (Rawhide); no upstream fix yet
Patch0:         howdy-rubberstamps-exec-module.patch
# nod.py: give the landmark predictor a rectangle when use_cnn is on;
# rubberstamps: a stamp that raises rejects the login instead of being skipped.
# No upstream fix yet
Patch1:         howdy-rubberstamps-fail-closed.patch
# A misspelled, missing or empty stamp rule must not bypass the extra check
Patch2:         howdy-rubberstamps-reject-invalid-rules.patch

BuildRequires:  gcc-c++
BuildRequires:  meson
BuildRequires:  gettext
BuildRequires:  bzip2
BuildRequires:  python3-devel
BuildRequires:  pam-devel
BuildRequires:  pkgconfig(INIReader)
BuildRequires:  pkgconfig(libevdev)
BuildRequires:  selinux-policy-devel

Requires:       %{name}-data = %{version}-%{release}
Requires:       python3dist(dlib)
Requires:       python3dist(numpy)
Requires:       python3dist(opencv)
Requires:       (%{name}-selinux = %{version}-%{release} if selinux-policy-%{selinuxtype})

%description
Howdy provides Windows Hello style authentication for Linux. It uses the
built-in IR emitters and camera together with face recognition to
authenticate the user through PAM.

The PAM module is installed but not enabled; see README.fedora for how to
configure the camera and add it to the PAM stack.


%package data
Summary:        Face models from dlib used by %{name}
License:        CC0-1.0
BuildArch:      noarch

%description data
Trained dlib models used by %{name}: 5-point face landmark predictor,
ResNet face recognition model and MMOD CNN face detector.


%package selinux
Summary:        SELinux policy module for %{name}
License:        MIT
BuildArch:      noarch
Requires:       selinux-policy-%{selinuxtype}
Requires(post): selinux-policy-%{selinuxtype}
%{?selinux_requires}

%description selinux
SELinux policy module that allows the display manager greeter and lock
screen (xdm_t) to use V4L2 cameras, so that %{name} works at the login and
lock screens with SELinux in enforcing mode.


%prep
%autosetup -p1 -n %{name}-%{commit}
for f in %{SOURCE10} %{SOURCE11} %{SOURCE12}; do
    bzip2 -dc "$f" > "howdy/src/dlib-data/$(basename "$f" .bz2)"
done
cp -p %{SOURCE13} dlib-models-LICENSE
mkdir selinux
cp -p %{SOURCE1} selinux/
cp -p %{SOURCE2} .


%build
# Python sources go to a private directory, not site-packages: they are
# scripts plus helper modules, not an importable package
%meson \
    -Dpy_sources_dir=%{_datadir} \
    -Ddlib_data_dir=%{_datadir}/%{name}/dlib-data \
    -Dpython_path=%{python3} \
    -Dinstall_in_site_packages=false \
    -Dwith_polkit=false \
    -Dinstall_pam_config=false
%meson_build

%make_build -C selinux -f %{_datadir}/selinux/devel/Makefile howdy.pp
bzip2 -9 selinux/howdy.pp


%install
%meson_install

# Downloader for the dlib models, which are shipped in howdy-data instead
rm %{buildroot}%{_datadir}/%{name}/dlib-data/{install.sh,Readme.md}
install -p -m 0644 howdy/src/dlib-data/*.dat %{buildroot}%{_datadir}/%{name}/dlib-data/

# howdy-gtk needs python3dist(elevate), which Fedora does not ship;
# compare.py runs fine without it
rm -r %{buildroot}%{_bindir}/%{name}-gtk \
      %{buildroot}%{_datadir}/%{name}-gtk

# meson skips config.ini if the build host already has one, and installs
# config.ini and the bash completion 0744
install -D -p -m 0644 howdy/src/config.ini %{buildroot}%{_sysconfdir}/%{name}/config.ini
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}/models
chmod 0644 %{buildroot}%{bash_completions_dir}/%{name}
# Completions are sourced, not executed
sed -i '1{/^#!/d}' %{buildroot}%{bash_completions_dir}/%{name}

# Precompile so running as root never writes __pycache__ under /usr/share
%py_byte_compile %{python3} %{buildroot}%{_datadir}/%{name}

install -D -p -m 0644 selinux/howdy.pp.bz2 \
    %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2


%check
# Every path compare.py will open at runtime must be shipped by this package
PYTHONPATH=%{buildroot}%{_datadir}/%{name} %{python3} - <<'EOF'
import os, paths_factory as p
for f in (p.shape_predictor_5_face_landmarks_path(),
          p.mmod_human_face_detector_path(),
          p.dlib_face_recognition_resnet_model_v1_path(),
          p.config_file_path(),
          str(p.user_models_dir_path())):
    assert os.path.exists("%{buildroot}" + f), f
EOF
grep -q '"%{_datadir}/%{name}/compare.py"' %{_vpath_builddir}/howdy/src/pam/paths.hh
grep -q '"%{python3}"' %{_vpath_builddir}/howdy/src/pam/paths.hh

# Rubberstamps with throwaway stamps: loading must not use deprecated
# importlib APIs, and a stamp that raises must reject (exit 15), not pass
stamps=$(mktemp -d)
cp -r %{buildroot}%{_datadir}/%{name}/{i18n.py,rubberstamps} "$stamps"
cat > "$stamps/rubberstamps/probe.py" <<'EOF'
from rubberstamps import RubberStamp
class probe(RubberStamp):
    def declare_config(self): pass
    def run(self):
        open(self.config.get("debug", "marker"), "w").close()
        return True
EOF
cat > "$stamps/rubberstamps/boom.py" <<'EOF'
from rubberstamps import RubberStamp
class boom(RubberStamp):
    def declare_config(self): pass
    def run(self): raise TypeError("stamp crashed")
EOF
cat > "$stamps/run.py" <<'EOF'
import configparser, sys, rubberstamps
config = configparser.ConfigParser()
config.read_dict({"rubberstamps": {"stamp_rules": sys.argv[1]},
                  "debug": {"marker": sys.argv[2]}})
rubberstamps.execute(config, None, dict.fromkeys(
    ["video_capture", "face_detector", "pose_predictor", "clahe"]))
EOF
PYTHONPATH="$stamps" %{python3} -W error::DeprecationWarning "$stamps/run.py" "probe 1s failsafe" "$stamps/ran"
test -e "$stamps/ran"
rc=0
PYTHONPATH="$stamps" %{python3} "$stamps/run.py" "boom 1s faildeadly" "$stamps/ran" || rc=$?
test $rc -eq 15
for bad_rule in "nodd 1s failsafe" "invalid" "" \
                "probe 1s failsafe missing=1" "probe 1s unknown"; do
    rc=0
    PYTHONPATH="$stamps" %{python3} "$stamps/run.py" "$bad_rule" "$stamps/ran" || rc=$?
    test $rc -eq 15
done


%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2

%postun selinux
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall -s %{selinuxtype} %{name}
fi


%files
%license LICENSE
%doc README.md README.fedora
%{_bindir}/%{name}
%{_libdir}/security/pam_%{name}.so
%dir %{_datadir}/%{name}/
%{_datadir}/%{name}/*.py
%{_datadir}/%{name}/__pycache__/
%{_datadir}/%{name}/cli/
%{_datadir}/%{name}/recorders/
%{_datadir}/%{name}/rubberstamps/
%{_datadir}/%{name}/logo.png
%{bash_completions_dir}/%{name}
%{_mandir}/man1/%{name}.1*
%dir %{_sysconfdir}/%{name}/
%dir %{_sysconfdir}/%{name}/models/
%config(noreplace) %{_sysconfdir}/%{name}/config.ini

%files data
%license dlib-models-LICENSE
%dir %{_datadir}/%{name}/
%{_datadir}/%{name}/dlib-data/

%files selinux
%license LICENSE
%{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{name}


%changelog
* Thu Sep 24 2026 Alvaro Garcia Infante <alvarogarciainfante@gmail.com> - 3.0.0-6
- Clarify model removal and the rubberstamp timeout modes in README.fedora

* Thu Sep 24 2026 Alvaro Garcia Infante <alvarogarciainfante@gmail.com> - 3.0.0-5
- Reject empty and invalid rubberstamp rules instead of bypassing the check

* Thu Sep 24 2026 Alvaro Garcia Infante <alvarogarciainfante@gmail.com> - 3.0.0-4
- Fix the nod rubberstamp with use_cnn = true
- Reject authentication when a rubberstamp raises instead of skipping it

* Wed Sep 23 2026 Alvaro Garcia Infante <alvarogarciainfante@gmail.com> - 3.0.0-3
- Load rubberstamps with exec_module(); load_module() is gone in Python 3.15
- Ship the license in howdy-selinux
- README.fedora: keep mandatory second factors, fix model permissions for KDE

* Wed Sep 23 2026 Alvaro Garcia Infante <alvarogarciainfante@gmail.com> - 3.0.0-2
- Add README.fedora with camera setup, enrollment and manual PAM activation
- Document the ffmpeg/pyv4l2 recorders and hotkey rubberstamp as unsupported

* Wed Sep 23 2026 Alvaro Garcia Infante <alvarogarciainfante@gmail.com> - 3.0.0-1
- Initial package, based on upstream commit d3ab993 (Release 3.0.0)
