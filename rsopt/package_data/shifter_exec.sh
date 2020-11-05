ulimit -c 0
unset PYTHONPATH
unset PYTHONSTARTUP
unset LESSCLOSE 
unset LESSOPEN
unset LESS
export PYENV_ROOT=/home/vagrant/.pyenv
export HOME=/home/vagrant
source /home/vagrant/.bashrc >& /dev/null
eval export HOME=~$USER
if [[ ! $LD_LIBRARY_PATH =~ /usr/lib64/mpich/lib ]]; then
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64/mpich/lib
fi

exec "$@"