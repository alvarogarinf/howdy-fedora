# howdy-fedora

RPM packaging of [Howdy](https://github.com/boltgolt/howdy) 3.0.0 (Windows
Hello style face authentication through PAM) for Fedora 44 and 45 (x86_64),
published as a COPR repository. This repository contains only build recipes;
sources are downloaded from upstream. Rawhide builds are also maintained
when its dependencies allow it.

## Install

```sh
sudo dnf copr enable alvarogarinf/howdy
sudo dnf install howdy
```

The package does **not** enable face authentication. Follow
[howdy/README.fedora](howdy/README.fedora), also installed as
`/usr/share/doc/howdy/README.fedora`, to configure the camera, enroll your
face and add `pam_howdy.so` to the PAM services you choose (sudo, GDM,
SDDM, Plasma Login, lock screens). The password always remains available.

Fedora 44 uses Python 3.14 and Fedora 45 uses Python 3.15. Each needs its
own build of `python3-dlib`; do not install Fedora 44 RPMs or use the
Rawhide repository on Fedora 45. If `dnf copr enable` reports a missing
chroot, the maintainer must enable and build that Fedora target first.
See section 7 of [README.fedora](howdy/README.fedora) if Howdy was removed
during the OS upgrade.

**Do not use it on services that require a second factor** (for example
authselect's `with-pam-u2f-2fa`): the recipe uses `sufficient`, so a
recognised face would skip both the password and the security key.

## Packages

| Package          | Contents                                                        |
|------------------|-----------------------------------------------------------------|
| `python3-dlib`   | dlib Python bindings for the system Python (`python3dist(dlib)`) |
| `howdy`          | CLI, `compare.py` and `pam_howdy.so` in `%{_libdir}/security`   |
| `howdy-data`     | dlib face models (CC0-1.0)                                      |
| `howdy-selinux`  | SELinux module letting `xdm_t` use V4L2 cameras; installed automatically on SELinux systems |

## Not supported

- `recording_plugin = ffmpeg` or `pyv4l2`, and the `hotkey` rubberstamp:
  their Python dependencies are not in Fedora.
- `howdy-gtk`.

## License

Original packaging files and documentation in this repository are licensed
under [MIT](LICENSE). The Howdy and dlib source archives and the dlib models
retain their respective upstream licenses, recorded in the RPM specs.

## Build

`python3-dlib` must be built first. Run the following for each target:
`fedora-44-x86_64`, `fedora-45-x86_64` and `fedora-rawhide-x86_64`.
Keep separate repositories and results so a dependency from another Fedora
release cannot be selected. Build dependencies are installed only inside
Mock, not on the host.

```sh
set -e
target=fedora-45-x86_64
resultdir="$PWD/results/$target"
mkdir -p "$resultdir/srpm"

# python-dlib
spectool -g -C python-dlib python-dlib/python-dlib.spec
rpmbuild -bs --define "_sourcedir $PWD/python-dlib" --define "_srcrpmdir $resultdir/srpm" python-dlib/python-dlib.spec
dlib_srpm=$(rpmspec -q --srpm --qf '%{name}-%{version}-%{release}.src.rpm' python-dlib/python-dlib.spec)
mock -r "$target" --resultdir="$resultdir/python-dlib" --rebuild "$resultdir/srpm/$dlib_srpm"

# local repository with the dlib RPM, for building and testing howdy
mkdir -p "$resultdir/repo"
cp "$resultdir"/python-dlib/python3-dlib-[0-9]*.x86_64.rpm "$resultdir/repo/"
createrepo_c --update "$resultdir/repo"

# howdy
spectool -g -C howdy howdy/howdy.spec
rpmbuild -bs --define "_sourcedir $PWD/howdy" --define "_srcrpmdir $resultdir/srpm" howdy/howdy.spec
howdy_srpm=$(rpmspec -q --srpm --qf '%{name}-%{version}-%{release}.src.rpm' howdy/howdy.spec)
mock -r "$target" --addrepo="file://$resultdir/repo" --resultdir="$resultdir/howdy" --rebuild "$resultdir/srpm/$howdy_srpm"

rpmlint python-dlib/python-dlib.spec "$resultdir"/python-dlib/*.rpm
# the justification for every filtered howdy warning is in howdy/howdy.rpmlintrc
rpmlint -r howdy/howdy.rpmlintrc howdy/howdy.spec "$resultdir"/howdy/*.rpm
```

The SRPM filename reflects the build host's `%dist`; Mock rebuilds it for
the chosen target. Python paths, bytecode and the native dlib ABI are
selected by that target's RPM macros. The generated `python(abi)` dependency
is required for dlib and must not be removed.

`python-dlib` runs the upstream tests with NumPy enabled. Howdy's `%check`
loads all three models and exercises OpenCV, NumPy, both face detectors and
face descriptor generation without a camera. These checks do not replace
testing login and password fallback on real hardware with SELinux enforcing.

The `obsolete-not-provided howdy-gtk` lint warning is intentional: `Obsoletes`
allows upgrades from other COPRs whose GTK package pins their Howdy build.
This package does not provide that interface, so it must not claim to.

## Publish in COPR

There is no CI workflow or automatic build submission in this repository.
Enable all supported chroots explicitly; `modify --chroot` replaces the
existing selection, so retain Fedora 44 and Rawhide:

```sh
copr-cli modify alvarogarinf/howdy \
    --chroot fedora-44-x86_64 \
    --chroot fedora-45-x86_64 \
    --chroot fedora-rawhide-x86_64 \
    --follow-fedora-branching on
```

After local validation, publish the SRPMs built above. These commands wait
for completion. Only submit Howdy if dlib succeeds, so Howdy's build checks
can use the new native dlib package in each chroot. Publish stable Fedora
and Rawhide separately so a Rawhide failure does not block stable builds:

```sh
copr-cli build -r fedora-44-x86_64 -r fedora-45-x86_64 \
    alvarogarinf/howdy "$resultdir/srpm/$dlib_srpm" &&
    copr-cli build -r fedora-44-x86_64 -r fedora-45-x86_64 \
        alvarogarinf/howdy "$resultdir/srpm/$howdy_srpm"

copr-cli build -r fedora-rawhide-x86_64 \
    alvarogarinf/howdy "$resultdir/srpm/$dlib_srpm" &&
    copr-cli build -r fedora-rawhide-x86_64 \
        alvarogarinf/howdy "$resultdir/srpm/$howdy_srpm"
```

Do not add `--nowait` to this sequence. After a new Fedora branch is enabled,
rebuild both packages in order; enabling a chroot alone does not produce
native RPMs. A failure on Rawhide needs investigation before claiming
support for its current dependencies.
