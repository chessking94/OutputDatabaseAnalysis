import logging
import os


def validate_corrflag(corrflag):
    corrflag = str(corrflag)
    corrflag_list = ['0', '1']
    if corrflag not in corrflag_list:
        logging.warning(f'Unknown corrflag value of {corrflag} was passed, converted to 0')
        corrflag = '0'
    return corrflag


def validate_depth(depth):
    max_depth = 25
    if not isinstance(depth, int):
        logging.critical(f'Depth {depth} is not an integer')
        raise SystemExit
    if depth % 2 != 1:  # only want odd depths, work better with engines
        depth = depth - 1
    if depth > max_depth:
        logging.critical(f'Depth {depth} is greater than the max depth of {max_depth}')
        raise SystemExit
    return depth


def validate_file(path, file):
    if not os.path.isfile(os.path.join(path, file)):
        logging.critical(f'File {file} does not exist at {path}')
        raise SystemExit
    return file


def validate_gametype(type):
    type_list = ['Control', 'EEH', 'Online', 'Test']
    if type not in type_list:
        logging.critical(f'Invalid game type {type} provided')
        raise SystemExit
    return type


def validate_path(path, type):
    if not os.path.isdir(path):
        if type == 'root':
            logging.info(f'Created new analysis directory {path}')
            os.mkdir(os.path.join(path, 'PGN', 'Archive'))
            os.mkdir(os.path.join(path, 'Output', 'Archive'))
        elif type == 'engine':
            logging.critical(f'Engine directory {path} does not exist')
            raise SystemExit
        else:
            logging.critical(f'Unknown directory type {type} passed')
            raise SystemExit
    return path
