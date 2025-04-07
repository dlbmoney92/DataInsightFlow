{pkgs}: {
  deps = [
    pkgs.postgresql
    pkgs.tk
    pkgs.tcl
    pkgs.qhull
    pkgs.gtk3
    pkgs.gobject-introspection
    pkgs.ghostscript
    pkgs.freetype
    pkgs.ffmpeg-full
    pkgs.cairo
    pkgs.arrow-cpp
    pkgs.jre
    pkgs.glibcLocales
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
  ];
}
