from github import Github

def try_update(current_version: str):
    g = Github()
    repo = g.get_repo("iNateee/to_do")

    print(f'stars: {repo.stargazers_count}')