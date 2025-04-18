import gitlab
import csv
import os

# GitLab setup using environment variables for security
GITLAB_URL = os.getenv("CI_SERVER_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("CI_JOB_TOKEN")  # Or use your personal token

# Connect to GitLab
gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_TOKEN)

def fetch_group_ldap_mappings():
    """Fetch LDAP group mappings for each GitLab group and export to CSV."""
    groups_data = []
    
    # Fetch all groups
    groups = gl.groups.list(all=True)
    
    for group in groups:
        try:
            # Fetch LDAP group links for the GitLab group
            ldap_links = group.ldap_group_links.list()
            for link in ldap_links:
                groups_data.append({
                    "Group Name": group.name,
                    "Group ID": group.id,
                    "LDAP Group": link.cn,
                    "Access Level": link.group_access
                })
        except gitlab.exceptions.GitlabGetError:
            print(f"Unable to fetch LDAP links for group: {group.name}")
    
    # Write to CSV
    with open('gitlab_group_ldap_mappings.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ["Group Name", "Group ID", "LDAP Group", "Access Level"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(groups_data)

    print("LDAP mappings have been exported to 'gitlab_group_ldap_mappings.csv'.")

if __name__ == "__main__":
    fetch_group_ldap_mappings()
