# Upstream KISS FFT, only for its license notice; dlib compiles a copy of it
%global kissfft_commit  e5e3fac46e0d94a8f8170c06706b7a4218828333

Name:           python-dlib
Version:        20.0.1
Release:        2%{?dist}
Summary:        Python bindings for the dlib machine learning toolkit

# dlib is BSL-1.0 except:
#   dlib/fft/kiss_fft.h: BSD-3-Clause
#   pybind11 headers compiled into the module: BSD-3-Clause
#   dlib/general_hash/murmur_hash3.h: MurmurHash3 algorithm, public domain
License:        BSL-1.0 AND BSD-3-Clause AND LicenseRef-Fedora-Public-Domain
URL:            http://dlib.net
Source0:        https://github.com/davisking/dlib/archive/v%{version}/dlib-%{version}.tar.gz
Source1:        https://raw.githubusercontent.com/mborgerding/kissfft/%{kissfft_commit}/COPYING#/kissfft-COPYING
Source2:        https://raw.githubusercontent.com/mborgerding/kissfft/%{kissfft_commit}/LICENSES/BSD-3-Clause#/kissfft-BSD-3-Clause
# Fedora-specific, not suitable upstream:
# - build against the system pybind11 instead of the bundled copy
# - link BLAS/LAPACK through FlexiBLAS, per Fedora BLAS policy
# - do not enable SSE4/AVX based on the build host CPU
# - do not let pybind11 strip the module, so debuginfo can be extracted
Patch0:         dlib-fedora.patch

BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  pkgconfig
BuildRequires:  python3-devel
BuildRequires:  python3-pytest
BuildRequires:  pybind11-devel
BuildRequires:  pkgconfig(flexiblas)
BuildRequires:  pkgconfig(libjpeg)
BuildRequires:  pkgconfig(libpng)

%global _description %{expand:
dlib is a modern C++ toolkit containing machine learning algorithms and
tools for creating complex software to solve real world problems. This
package provides its Python bindings, including face detection, facial
landmark prediction and face recognition.}

%description %_description

%package -n     python3-dlib
Summary:        %{summary}
# Copy of KISS FFT in dlib/fft/kiss_fft.h
Provides:       bundled(kissfft)

%description -n python3-dlib %_description


%prep
%autosetup -p1 -n dlib-%{version}
# Bundled pybind11, cblas, libjpeg, libpng and zlib; the system ones are used
rm -r dlib/external
cp -p %{SOURCE1} %{SOURCE2} .
cp -p %{_licensedir}/pybind11-devel/LICENSE pybind11-LICENSE


%generate_buildrequires
%pyproject_buildrequires


%build
# setup.py forwards every DLIB_* environment variable to CMake
export DLIB_NO_GUI_SUPPORT=ON
export DLIB_USE_CUDA=OFF
export DLIB_USE_BLAS=ON
export DLIB_USE_LAPACK=ON
export DLIB_USE_MKL_FFT=OFF
export DLIB_JPEG_SUPPORT=ON
export DLIB_PNG_SUPPORT=ON
export DLIB_GIF_SUPPORT=OFF
export DLIB_WEBP_SUPPORT=OFF
export DLIB_JXL_SUPPORT=OFF
export DLIB_LINK_WITH_SQLITE3=OFF
# Each compiler process needs up to ~2 GiB of RAM
%constrain_build -m 2048
export CMAKE_BUILD_PARALLEL_LEVEL=%{_smp_build_ncpus}
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -l dlib _dlib_pybind11


%check
%pyproject_check_import
%pytest tools/python/test


%files -n python3-dlib -f %{pyproject_files}
%doc README.md
%license kissfft-COPYING kissfft-BSD-3-Clause pybind11-LICENSE


%changelog
* Wed Sep 23 2026 Alvaro Garcia Infante <alvarogarciainfante@gmail.com> - 20.0.1-2
- Ship the license notices of the bundled KISS FFT and of pybind11

* Wed Sep 23 2026 Alvaro Garcia Infante <alvarogarciainfante@gmail.com> - 20.0.1-1
- Initial package
