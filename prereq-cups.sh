# Gain root
sudo su -
### Install pre-requisites
# Remove existing gutenprint packages and ipp-usb
apt remove *gutenprint* ipp-usb
# Install necessary development libraries
apt install libusb-1.0-0-dev libcups2-dev pkg-config
# Install CUPS (just in case)
apt install cups-daemon
# Install git-lfs
apt install git-lfs
# Install curl
apt install curl
### Download and compile Gutenprint
# Download latest gutenprint snapshot from sourceforge
GUTENPRINT_VER=5.3.5-pre1-2025-02-13T14-28-b60f1e83
curl -o gutenprint-${GUTENPRINT_VER}.tar.xz "https://master.dl.sourceforge.net/project/gimp-print/snapshots/gutenprint-${GUTENPRINT_VER}.tar.xz?viasf=1"
# Decompress & Extract
tar -xJf gutenprint-${GUTENPRINT_VER}.tar.xz
# Compile gutenprint
cd gutenprint-${GUTENPRINT_VER}
./configure --without-doc --enable-debug
make -j4
make install
cd ..
# Refresh PPDs
cups-genppdupdate
# Restart CUPS
service cups restart
## At this point you can stop unless you have certian Mitsubishi, Sinfonia, Fujifilm, and Hiti models)
### Download and compile latest backend code
# Get the latest selphy_print code
git clone https://git.shaftnet.org/gitea/slp/selphy_print.git
# Compile selphy_print
cd selphy_print
make -j4 
make install
# Set up library include path
echo "/usr/local/lib" > /etc/ld.so.conf.d/usr-local.conf
ldconfig
# FiN
exit