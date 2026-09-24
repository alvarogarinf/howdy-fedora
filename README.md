# howdy-fedora

RPM packaging of [Howdy](https://github.com/boltgolt/howdy) 3.0.0 (Windows
Hello style face authentication through PAM) for Fedora 44, published as a
COPR repository. This repository contains only build recipes; sources are
downloaded from upstream.

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

`python3-dlib` must be built first.

```sh
# python-dlib
spectool -g -C python-dlib python-dlib/python-dlib.spec
rpmbuild -bs --define "_sourcedir $PWD/python-dlib" --define "_srcrpmdir $PWD/results/srpm" python-dlib/python-dlib.spec
mock -r fedora-44-x86_64 --resultdir=results/python-dlib --rebuild results/srpm/python-dlib-*.src.rpm

# local repository with the dlib RPM, for building and testing howdy
mkdir -p results/repo && cp results/python-dlib/python3-dlib-*.x86_64.rpm results/repo/ && createrepo_c results/repo

# howdy
spectool -g -C howdy howdy/howdy.spec
rpmbuild -bs --define "_sourcedir $PWD/howdy" --define "_srcrpmdir $PWD/results/srpm" howdy/howdy.spec
mock -r fedora-44-x86_64 --addrepo=file://$PWD/results/repo --resultdir=results/howdy --rebuild results/srpm/howdy-*.src.rpm

rpmlint python-dlib/python-dlib.spec results/python-dlib/*.rpm
# the justification for every filtered howdy warning is in howdy/howdy.rpmlintrc
rpmlint -r howdy/howdy.rpmlintrc howdy/howdy.spec results/howdy/*.rpm
```
