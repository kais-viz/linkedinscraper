def is_running_in_docker():
    """
    Check if the application is running inside a Docker container.
    Returns True if running in Docker, False otherwise.
    """
    try:
        # Check for the existence of /.dockerenv file
        with open('/.dockerenv', 'r') as f:
            return True
    except IOError:
        # Check for cgroup which might indicate Docker
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read()
        except IOError:
            return False
    return False

def get_db_host(config):
    """
    Returns the appropriate database host based on the environment.
    If running in Docker, returns host_docker, otherwise returns host_local.
    """
    if is_running_in_docker():
        return config.get('host_docker', 'db')
    else:
        return config.get('host_local', 'localhost')
