import os


def main():
    tst_cmd = 'python -m unittest discover'
    root_dir = os.path.dirname(__file__)
    if os.getcwd() != root_dir:
        os.chdir(root_dir)
    os.system('cmd /C ' + tst_cmd)


if __name__ == '__main__':
    main()
