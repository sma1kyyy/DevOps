#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
import re
import os

def main():
    module = AnsibleModule(
        argument_spec=dict(
            port=dict(type='int', required=True),
            config_path=dict(type='str', default='/etc/nginx/nginx.conf')
        ),
        supports_check_mode=True 
    )
    
    port = module.params['port']
    path = module.params['config_path']
    changed = False

    if not os.path.exists(path):
        module.fail_json(msg=f"Config file not found at {path}")

    with open(path, 'r') as f:
        content = f.read()

    new_content = re.sub(r'listen\s+\d+;', f'listen {port};', content)

    if new_content != content:
        changed = True
        if not module.check_mode:
            with open(path, 'w') as f:
                f.write(new_content)

    module.exit_json(changed=changed, port=port, path=path)

if __name__ == '__main__':
    main()