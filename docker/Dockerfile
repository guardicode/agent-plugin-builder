# NOTE: pywine wine prefix location is stored in the WINEPREFIX env variable
# NOTE: It also installs the wine prefix with 777 permissions
FROM pywine:3.11

# Install git into the wine prefix
RUN cd /tmp && \
    umask 0 && \
    curl -Lo mingit.zip https://github.com/git-for-windows/git/releases/download/v2.45.1.windows.1/MinGit-2.45.1-64-bit.zip && \
    unzip mingit.zip -d $WINEPREFIX/drive_c/git && \
    rm mingit.zip

# Make git available in the wine prefix's PATH
ENV WINEPATH=C:\\git\\cmd

RUN useradd wineuser
USER wineuser
