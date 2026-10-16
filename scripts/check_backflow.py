#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_backflow.py —— 回流两连核销守卫（坑 46/47 的机械化根治，v1.5.2）

背景（2026-10-16 sz02 实证）：收官回写 ≠ 回流到位。宣称"回写完成"但 skill 仓
未 commit/push、成果未注册 VOLUME_META、双仓未同步、线上未终验——四层缺口
任何一处静默漏掉，问题会在下下卷才暴露。文档（pitfalls/CHANGELOG）防不了
"忘了跑"，只有逐项核销的守卫脚本能防。

用法：
  python check_backflow.py <卷key>            # 全链核销（含线上终验）
  python check_backflow.py <卷key> --offline  # 跳过线上 API（服务器维护期）

核销四层（全绿才 PASS，任一缺口即 FAIL 并给出修复动作）：
  A. skill 仓     git status 干净 + 本地 main == origin/main + 最新 CHANGELOG 版本有 tag
  B. 成果注册     sync_remote.py VOLUME_META 有该卷条目
  C. 双仓本地态   .volumes_data_repo/.volumes_repo 干净 + volumes.json 的 sha256 == 本地权威 db
  D. 线上终验     /api/quota/volumes 有该卷 + items 数与本地一致 + book_name 为全称
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request

SP = r"C:/Users/Administrator/WorkBuddy/sp"
SKILL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SYNC = os.path.join(SP, "sync_remote.py")
REPO = os.path.join(SP, ".volumes_repo")
REPO_DATA = os.path.join(SP, ".volumes_data_repo")
ONLINE = "http://134.175.50.9:3001/api/quota/volumes"

# 卷目录名注册表口径与 sync_remote.py 一致（quota-extract-<key>）
RESULTS = []


def sh(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=60,
                       text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def check(name, ok, detail, fix):
    RESULTS.append(ok)
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}: {detail}")
    if not ok:
        print(f"       → 修复: {fix}")


def git_state(repo, label):
    """返回 (clean, synced, local, remote, mode)
    synced 判定优先 ls-remote 网络实查（API 通道推送成功但本地 origin/main
    引用不前移——api_push_public.py 已知特性，rev-parse 会误报）；网络失败
    才回退 origin/main 并注明。"""
    _, out, _ = sh(["git", "status", "--porcelain"], cwd=repo)
    clean = not out
    _, local, _ = sh(["git", "rev-parse", "main"], cwd=repo)
    _, out, _ = sh(["git", "ls-remote", "origin", "refs/heads/main"], cwd=repo)
    if out:
        remote = out.split()[0]
        if local == remote:
            return clean, True, local, remote, "ls-remote"
        # sha 不等：API 通道双轨 commit（api_push_public 本地无对象）——验证 tree 等价
        _, ltree, _ = sh(["git", "rev-parse", "main^{tree}"], cwd=repo)
        rtree = _remote_tree(repo, remote)
        if rtree and ltree == rtree:
            return clean, True, local, remote, "ls-remote+tree等价(API双轨)"
        return clean, False, local, remote, "ls-remote"
    # ls-remote 也 502：经 API 直查远端真实 main sha。
    # 不能用本地 origin/main 引用——API 通道推送后本地无该 commit 对象，
    # update-ref 必失败，引用永远陈旧（xj01 实证：本地 ref 停在推送前 sha，
    # 回退比 ref→误报未同步）。
    remote = _remote_main(repo)
    if remote:
        _, ltree, _ = sh(["git", "rev-parse", "main^{tree}"], cwd=repo)
        if local == remote:
            return clean, True, local, remote, "API ref"
        rtree = _remote_tree(repo, remote)
        if rtree and ltree == rtree:
            return clean, True, local, remote, "API ref+tree等价(API双轨)"
        return clean, False, local, remote, "API ref"
    _, remote, _ = sh(["git", "rev-parse", "origin/main"], cwd=repo)
    if local == remote:
        return clean, True, local, remote, "origin/main"
    _, ltree, _ = sh(["git", "rev-parse", "main^{tree}"], cwd=repo)
    rtree = _remote_tree(repo, remote)
    if rtree and ltree == rtree:
        return clean, True, local, remote, "origin/main+tree等价(API双轨)"
    return clean, False, local, remote, "origin/main(回退)"


def _slug(repo):
    m = re.search(r"github\.com[/:]([^/]+/[^.]+?)(?:\.git)?/?$",
                  sh(["git", "remote", "get-url", "origin"], cwd=repo)[1])
    return m.group(1) if m else None


def _auth_headers():
    headers = {"User-Agent": "backflow-check", "Accept": "application/vnd.github+json"}
    try:
        r = subprocess.run(["git", "credential", "fill"],
                           input="protocol=https\nhost=github.com\n\n",
                           capture_output=True, timeout=30, text=True)
        tok = next((l.split("=", 1)[1] for l in r.stdout.splitlines()
                    if l.startswith("password=")), "")
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
    except Exception:
        pass
    return headers


def _remote_main(repo):
    """经 GitHub API 查远端真实 main sha（ls-remote 502 时的替代通道）"""
    slug = _slug(repo)
    if not slug:
        return None
    try:
        import urllib.request
        req = urllib.request.Request(
            f"https://api.github.com/repos/{slug}/git/refs/heads/main",
            headers=_auth_headers())
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp).get("object", {}).get("sha")
    except Exception:
        return None


def _remote_tree(repo, commit_sha):
    """经 GitHub API 取远端 commit 的 tree sha（tree 等价降级判定用）"""
    slug = _slug(repo)
    if not slug:
        return None
    import urllib.request
    try:
        # 私有仓匿名 404 → 带 git credential token（与 git_api_push.py 同通道）
        req = urllib.request.Request(
            f"https://api.github.com/repos/{slug}/git/commits/{commit_sha}",
            headers=_auth_headers())
        return json.load(urllib.request.urlopen(req, timeout=15)).get("tree", {}).get("sha")
    except Exception:
        return None


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print(__doc__)
        sys.exit(2)
    key = sys.argv[1]
    offline = "--offline" in sys.argv

    # ---- B. 成果注册（先查注册表拿到权威 db 路径）----
    src = open(SYNC, encoding="utf-8").read()
    m = re.search(r'"quota-extract-%s":\s*\(([^)]*)\)' % re.escape(key), src)
    check("B 成果注册 VOLUME_META", bool(m),
          f"quota-extract-{key} " + ("已注册" if m else "未注册"),
          f'sync_remote.py VOLUME_META 加一行 "quota-extract-{key}": (key, kind, label)')

    # ---- C. 双仓本地态 + volumes.json 指纹一致 ----
    reg_path = os.path.join(REPO, "volumes.json")
    entry = None
    if os.path.exists(reg_path):
        reg = json.load(open(reg_path, encoding="utf-8"))
        for region in reg.get("regions", []):
            for v in region.get("volumes", []):
                if v["key"] == key:
                    entry = v
    if entry is None:
        check("C volumes.json 条目", False, f"key={key} 不在注册表", "跑 sync_remote.py 生成/同步 volumes.json")
    else:
        # entry["db"] 形如 liaoning-2024/<卷目录>/db_pdf|db_docx/<file>.db（仓内路径）
        # 本地权威库=SP/<卷目录>/out|docx_source/<file>.db（site_db 同口径）
        parts = entry["db"].split("/")
        voldir, dbfile = parts[1], parts[-1]
        cands = [os.path.join(SP, voldir, sub, dbfile) for sub in ("out", "docx_source")]
        db_local = next((p for p in cands if os.path.exists(p) and os.path.getsize(p) > 0), None)
        ok_db = os.path.exists(db_local) and os.path.getsize(db_local) > 0
        sha_local = hashlib.sha256(open(db_local, "rb").read()).hexdigest() if ok_db else ""
        check("C 权威 db 存在且非空", ok_db,
              f"{entry['db']} ({entry.get('bytes','?')}B)" + ("" if ok_db else " —— 0字节/缺失"),
              "检查卷目录 out/*.db；0 字节空壳=坑 47（诊断误建），删除后重跑 finalize")
        check("C volumes.json sha256 门禁", ok_db and sha_local == entry.get("sha256"),
              f"reg={entry.get('sha256','')[:12]} local={sha_local[:12]}",
              "重跑 sync_remote.py 刷新注册表指纹")
        # 双仓 git 干净且已推
        for repo, label in ((REPO_DATA, "私有仓"), (REPO, "公开仓")):
            clean, synced, local, remote, mode = git_state(repo, label)
            check(f"C {label} git 干净已推", clean and synced,
                  f"clean={clean} synced={synced}（{mode}）local={local[:8]} remote={remote[:8]}",
                  "重跑 sync_remote.py；git 502 时走 api_push_public.py [repo] [owner/repo]")

    # ---- A. skill 仓（回写到位）----
    clean, synced, local, remote, mode = git_state(os.path.abspath(SKILL), "skill仓")
    check("A skill 仓 git 干净已推", clean and synced,
          f"clean={clean} synced={synced}（{mode}）local={local[:8]} remote={remote[:8]}",
          "git add -A && git commit && git tag vX.Y.Z && git push --tags")
    # 最新 CHANGELOG 版本必须有 tag（防"改了文件没打版"）
    ch = open(os.path.join(SKILL, "CHANGELOG.md"), encoding="utf-8").read()
    m = re.search(r"^## (v[\d.]+)", ch, re.M)
    if m:
        latest = m.group(1)
        _, out, _ = sh(["git", "tag"], cwd=os.path.abspath(SKILL))
        check("A 最新 CHANGELOG 版本已打 tag", latest in out.split(),
              f"CHANGELOG 最新 {latest}，tags 含={latest in out.split()}",
              f"git tag {latest} && git push origin {latest}")
    # 本卷收官记录已入 CHANGELOG（防"卷完成但回写没进版本"）
    check("A 本卷已入 CHANGELOG", bool(re.search(r"^## .*" + re.escape(key), ch, re.M)),
          f"CHANGELOG 含 {key} 条目",
          "按迭代协议三件准入制（根因/根治/验证证据）回写后 commit")

    # ---- D. 线上终验 ----
    if offline:
        print("[SKIP] D 线上终验（--offline）")
    else:
        try:
            req = urllib.request.Request(ONLINE, headers={"User-Agent": "backflow-check"})
            vols = json.load(urllib.request.urlopen(req, timeout=15))["data"]
            v = next((x for x in vols if x["vol"] == key), None)
            if v is None:
                check("D 线上收录", False, f"{key} 不在线上 {len(vols)} 卷", "服务器协同补跑 + kill node 拉起（见 contribution.md 三）")
            else:
                check("D 线上收录", True, f"{key} available={v['available']}", "-")
                n_local = None
                if entry:
                    import sqlite3
                    if db_local:
                        con = sqlite3.connect(f"file:{db_local}?mode=ro", uri=True)  # 坑 47：只读 URI
                        try:
                            n_local = con.execute("select count(*) from items").fetchone()[0]
                        finally:
                            con.close()
                n_online = v["counts"]["items"]
                check("D 线上 items 数一致", n_local is None or n_local == n_online,
                      f"online={n_online} local={n_local}", "服务器 kill node 重启（动态注册表随进程生效）")
                # 坑46 全称判据卷自适应：「计价依据」是辽宁书名特有词，不可硬编码
                # （xj01 新疆卷书名无此词）——判据=含「定额/计价依据」且长度>10 且非 label 降级
                bn = v.get("book_name") or ""
                check("D 线上 book_name 全称",
                      ("定额" in bn or "计价依据" in bn) and len(bn) > 10 and bn != v.get("label"),
                      bn[:30], "坑 46：finalize 补纯文本 book_name 后重跑+重同步")
        except Exception as e:
            check("D 线上终验", False, f"API 不可达/异常: {e}", "确认服务器在线；维护期可用 --offline")

    n_pass = sum(RESULTS)
    print("=" * 46)
    print(f"回流核销: {n_pass}/{len(RESULTS)} PASS" + ("，全链到位" if n_pass == len(RESULTS) else "，存在缺口，禁止宣称收官"))
    sys.exit(0 if n_pass == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
