"""Generator 核心類別"""

from pathlib import Path


class Generator:
    """Manifest 驅動的專案產生器"""

    def __init__(self, manifest: dict, project_name: str, output_dir: str = ".",
                 dry_run: bool = False, no_compat: bool = False,
                 modules_filter: list[str] | None = None):
        self.manifest = manifest
        self.project_name = project_name
        self.root = Path(output_dir) / project_name
        self.dry_run = dry_run
        self.no_compat = no_compat
        self.modules_filter = modules_filter
        self.created_files: list[str] = []

    def create_file(self, path: Path, content: str):
        """建立檔案，支援 dry_run 模式"""
        rel = str(path)
        self.created_files.append(rel)
        if self.dry_run:
            print(f"  [F] {rel}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        # 模板常數在三引號字串內用 \\' 跳脫單引號，產出時還原為 '
        cleaned = content.replace("\\'", "'")
        path.write_text(cleaned, encoding="utf-8")
        print(f"  [OK] {rel}")

    def get_modules(self) -> list[str]:
        """取得要產出的模組清單（套用 CLI 覆蓋）"""
        modules = list(self.manifest["modules"])

        # --no-compat：移除 compat 模組
        if self.no_compat and "compat" in modules:
            modules.remove("compat")

        # --modules：只保留指定模組 + common
        if self.modules_filter:
            modules = [m for m in modules if m in self.modules_filter]

        return modules

    def run(self):
        """執行產出"""
        from .registry import MODULE_REGISTRY

        profile_name = self.manifest["name"]
        mode = "dry-run" if self.dry_run else "生成"
        print(f"\n[GEN] {mode} {profile_name} project: {self.root}\n")

        # 產出各模組
        modules = self.get_modules()
        for mod_name in modules:
            if mod_name not in MODULE_REGISTRY:
                print(f"  [WARN] unknown module: {mod_name}, skipped")
                continue
            MODULE_REGISTRY[mod_name](self)

        # 產出 common（web / data / docs / config files）
        from .registry import gen_common
        gen_common(self)

        # 摘要
        total = len(self.created_files)
        status = "preview" if self.dry_run else "generated"
        print(f"\n[DONE] {profile_name} project {status}: {total} files")

        if not self.dry_run:
            print(f"\n[NEXT] Post steps:")
            for i, step in enumerate(self.manifest.get("post_steps", []), 1):
                print(f"   {i}. {step.format(root=self.root)}")

        return self.created_files
