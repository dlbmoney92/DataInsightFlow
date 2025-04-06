{pkgs}: {
  deps = [
    pkgs.arrow-cpp
    pkgs.jre
    pkgs.glibcLocales
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
  ];
}
