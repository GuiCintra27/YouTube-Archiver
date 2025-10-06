import React, { useEffect, useMemo, useState } from "react";

export default function App() {
  type Form = {
    source: string;
    outDir: string;
    path?: string;
    fileName?: string;
    fmt: string;
    maxRes?: string;
    audioOnly: boolean;
    subs: boolean;
    autoSubs: boolean;
    subLangs: string;
    thumbnails: boolean;
    workers: string;
    limit?: string;
    dryRun: boolean;
    concurrentFragments: string;
    cookiesFile?: string;
    referer?: string;
    origin?: string;
    userAgent: string;
    driveUpload: boolean;
    driveRoot: string;
    driveCredentials: string;
    driveToken: string;
    uploadedLog: string;
  };

  const [form, setForm] = useState<Form>({
    source: "",
    outDir: "./downloads",
    path: "",
    fileName: "",
    fmt: "bestvideo+bestaudio/best",
    maxRes: "",
    audioOnly: false,
    subs: true,
    autoSubs: true,
    subLangs: "pt,en",
    thumbnails: true,
    workers: "2",
    limit: "",
    dryRun: false,
    concurrentFragments: "10",
    cookiesFile: "",
    referer: "",
    origin: "",
    userAgent: "yt-archiver",
    driveUpload: false,
    driveRoot: "YouTubeArchive",
    driveCredentials: "./credentials.json",
    driveToken: "./token.json",
    uploadedLog: "./uploaded.jsonl",
  });

  const [profileName, setProfileName] = useState("");
  const [profiles, setProfiles] = useState<string[]>([]);

  useEffect(() => {
    const saved = Object.keys(localStorage)
      .filter((k) => k.startsWith("ytarchiver:profile:"))
      .map((k) => k.replace("ytarchiver:profile:", ""));
    setProfiles(saved.sort());
  }, []);

  const on = (k: keyof Form) => (e: any) => {
    const t = e?.target;
    const val = t?.type === "checkbox" ? !!t.checked : t?.value ?? e;
    setForm((f) => ({ ...f, [k]: val }));
  };

  const shellQ = (s: string) => `"${s.replace(/(["$`\\\\])/g, "\\$1")}"`;
  const nonEmpty = (s?: string) => (s && s.trim().length ? s.trim() : "");

  const buildPythonCmd = useMemo(() => {
    if (!nonEmpty(form.source)) return "# preencha a URL de origem (source)";
    let cmd = `python main.py download ${shellQ(
      form.source
    )} \\\n  --out-dir ${shellQ(form.outDir)}`;

    const path = nonEmpty(form.path);
    const fname = nonEmpty(form.fileName);
    if (path) cmd += ` \\\n  --path ${shellQ(path)}`;
    if (fname) cmd += ` \\\n  --file-name ${shellQ(fname)}`;

    if (form.fmt && form.fmt !== "bv*+ba/b")
      cmd += ` \\\n  --fmt ${shellQ(form.fmt)}`;
    if (nonEmpty(form.maxRes)) cmd += ` \\\n  --max-res ${form.maxRes}`;

    if (!form.subs) cmd += ` \\\n  --no-subs`;
    if (!form.autoSubs) cmd += ` \\\n  --no-auto-subs`;
    if (form.subLangs && form.subLangs !== "pt,en")
      cmd += ` \\\n  --sub-langs ${shellQ(form.subLangs)}`;
    if (!form.thumbnails) cmd += ` \\\n  --no-thumbnails`;
    if (form.audioOnly) cmd += ` \\\n  --audio-only`;

    if (form.workers && form.workers !== "1")
      cmd += ` \\\n  --workers ${form.workers}`;
    if (nonEmpty(form.limit)) cmd += ` \\\n  --limit ${form.limit}`;
    if (form.dryRun) cmd += ` \\\n  --dry-run`;

    if (nonEmpty(form.cookiesFile))
      cmd += ` \\\n  --cookies-file ${shellQ(form.cookiesFile!)}`;
    if (nonEmpty(form.referer))
      cmd += ` \\\n  --referer ${shellQ(form.referer!)}`;
    if (nonEmpty(form.origin)) cmd += ` \\\n  --origin ${shellQ(form.origin!)}`;
    if (form.userAgent && form.userAgent !== "yt-archiver")
      cmd += ` \\\n  --user-agent ${shellQ(form.userAgent)}`;
    if (form.concurrentFragments && form.concurrentFragments !== "10")
      cmd += ` \\\n  --concurrent-fragments ${form.concurrentFragments}`;

    if (form.driveUpload) {
      cmd += ` \\\n  --drive-upload --drive-root ${shellQ(
        form.driveRoot
      )} \\\n  --drive-credentials ${shellQ(
        form.driveCredentials
      )} \\\n  --drive-token ${shellQ(
        form.driveToken
      )} \\\n  --uploaded-log ${shellQ(form.uploadedLog)}`;
    }

    const segs = [form.outDir, nonEmpty(form.path)].filter(Boolean);
    const name = form.fileName
      ? `${form.fileName} [%(id)s].%(ext)s`
      : `%(upload_date>%Y-%m-%d|0000-00-00)s - %(title).%(ext)s`;
    const archive_id = [segs.join("/"), name].filter(Boolean).join("/");

    cmd += `\\\n --archive-id ${shellQ(archive_id || "")}`;

    return cmd;
  }, [form]);

  const buildYtDlpCmd = useMemo(() => {
    if (!nonEmpty(form.source)) return "# preencha a URL de origem (source)";
    const parts: string[] = ["yt-dlp"];
    parts.push(
      "-N",
      form.concurrentFragments || "10",
      "--concurrent-fragments",
      form.concurrentFragments || "10"
    );
    if (nonEmpty(form.referer)) parts.push("--referer", form.referer!.trim());
    if (nonEmpty(form.origin))
      parts.push("--add-header", `Origin: ${form.origin!.trim()}`);
    if (form.userAgent && form.userAgent !== "yt-archiver")
      parts.push("--user-agent", form.userAgent);
    if (nonEmpty(form.cookiesFile))
      parts.push("--cookies", form.cookiesFile!.trim());
    const outBase = [form.outDir, nonEmpty(form.path)]
      .filter(Boolean)
      .join("/");
    let nameTmpl = nonEmpty(form.fileName)
      ? `${form.fileName!.trim()} [%(id)s].%(ext)s`
      : `%(upload_date>%Y-%m-%d|0000-00-00)s - %(title).180B [%(id)s].%(ext)s`;
    parts.push("-o", `${outBase ? outBase + "/" : ""}${nameTmpl}`);
    if (nonEmpty(form.maxRes)) {
      parts.push(
        "-f",
        `bestvideo[height<=${form.maxRes}]+bestaudio/best[height<=${form.maxRes}]`
      );
    } else {
      parts.push("-f", form.fmt || "bestvideo+bestaudio/best");
    }
    if (form.subs) parts.push("--write-subs");
    if (form.autoSubs) parts.push("--write-auto-subs");
    if (form.subLangs && form.subLangs !== "pt,en")
      parts.push("--sub-langs", form.subLangs);
    if (form.thumbnails) parts.push("--write-thumbnail");
    if (form.audioOnly)
      parts.push(
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0"
      );
    parts.push(form.source.trim());
    return parts.map((p) => (/\s/.test(p) ? shellQ(p) : p)).join(" ");
  }, [form]);

  const copy = async (txt: string) => {
    try {
      await navigator.clipboard.writeText(txt);
      alert("Copiado! ✨");
    } catch {}
  };

  const saveProfile = () => {
    const name = profileName.trim();
    if (!name) return;
    localStorage.setItem("ytarchiver:profile:" + name, JSON.stringify(form));
    if (!profiles.includes(name)) setProfiles((p) => [...p, name].sort());
  };
  const loadProfile = (name: string) => {
    const raw = localStorage.getItem("ytarchiver:profile:" + name);
    if (!raw) return;
    try {
      setForm(JSON.parse(raw));
    } catch {}
  };
  const deleteProfile = (name: string) => {
    localStorage.removeItem("ytarchiver:profile:" + name);
    setProfiles((p) => p.filter((x) => x !== name));
  };
  const previewPath = useMemo(() => {
    const segs = [form.outDir, nonEmpty(form.path)].filter(Boolean);
    const name = nonEmpty(form.fileName)
      ? `${form.fileName} [%(id)s].%(ext)s`
      : `%(upload_date>%Y-%m-%d|0000-00-00)s - %(title).%(ext)s`;
    return [segs.join("/"), name].filter(Boolean).join("/");
  }, [form]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold">
              yt-archiver — UI
            </h1>
            <p className="text-slate-600">
              Gere comandos para o seu script Python (ou yt-dlp) sem decorar
              flags. ✨
            </p>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section className="bg-white rounded-2xl shadow p-5 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Entrada & Destino</h2>
            <div className="space-y-3">
              <TextInput
                label="Source (URL ou arquivo .txt)"
                placeholder="https://.../playlist.m3u8 ou https://youtube.com/..."
                value={form.source}
                onChange={on("source")}
                required
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <TextInput
                  label="Saída (out-dir)"
                  value={form.outDir}
                  onChange={on("outDir")}
                />
                <TextInput
                  label="Subpasta (path)"
                  placeholder="rocketSeat/Go/Introdução"
                  value={form.path || ""}
                  onChange={on("path")}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <TextInput
                  label="Nome do arquivo (file-name)"
                  placeholder="Aula 01"
                  value={form.fileName || ""}
                  onChange={on("fileName")}
                />
                <TextInput
                  label="Prévia do caminho (somente visual)"
                  value={previewPath}
                  readOnly
                />
              </div>
            </div>

            <h2 className="text-lg font-semibold mt-6 mb-2">Qualidade</h2>
            <div className="space-y-3">
              <TextInput
                label="Format selector (fmt)"
                value={form.fmt}
                onChange={on("fmt")}
                helper="Ex.: bestvideo+bestaudio/best | bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
              />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <TextInput
                  label="Max Res (opcional)"
                  type="number"
                  min="144"
                  placeholder="1080"
                  value={form.maxRes || ""}
                  onChange={on("maxRes")}
                />
                <NumberInput
                  label="Workers (URLs em paralelo)"
                  value={form.workers}
                  onChange={on("workers")}
                  min={"1"}
                />
                <NumberInput
                  label="Concurrent fragments (-N)"
                  value={form.concurrentFragments}
                  onChange={on("concurrentFragments")}
                  min={"1"}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Checkbox
                  label="Baixar legendas"
                  checked={form.subs}
                  onChange={on("subs")}
                />
                <Checkbox
                  label="Incluir auto-subs"
                  checked={form.autoSubs}
                  onChange={on("autoSubs")}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <TextInput
                  label="Idiomas de legenda"
                  value={form.subLangs}
                  onChange={on("subLangs")}
                />
                <Checkbox
                  label="Salvar thumbnails"
                  checked={form.thumbnails}
                  onChange={on("thumbnails")}
                />
              </div>
              <Checkbox
                label="Áudio somente (MP3)"
                checked={form.audioOnly}
                onChange={on("audioOnly")}
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <NumberInput
                  label="Limite (N)"
                  value={form.limit || ""}
                  onChange={on("limit")}
                  min={"1"}
                />
                <Checkbox
                  label="Dry run (não baixa)"
                  checked={form.dryRun}
                  onChange={on("dryRun")}
                />
              </div>
            </div>

            <h2 className="text-lg font-semibold mt-6 mb-2">
              Headers & Cookies (opcional)
            </h2>
            <div className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <TextInput
                  label="Referer"
                  placeholder="https://iframe.mediadelivery.net/"
                  value={form.referer || ""}
                  onChange={on("referer")}
                />
                <TextInput
                  label="Origin"
                  placeholder="https://iframe.mediadelivery.net"
                  value={form.origin || ""}
                  onChange={on("origin")}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <TextInput
                  label="cookies.txt (opcional)"
                  placeholder="./cookies.txt"
                  value={form.cookiesFile || ""}
                  onChange={on("cookiesFile")}
                />
                <TextInput
                  label="User-Agent"
                  value={form.userAgent}
                  onChange={on("userAgent")}
                />
              </div>
            </div>

            <h2 className="text-lg font-semibold mt-6 mb-2">
              Google Drive (opcional)
            </h2>
            <div className="space-y-3">
              <Checkbox
                label="Fazer upload para o Google Drive"
                checked={form.driveUpload}
                onChange={on("driveUpload")}
              />
              {form.driveUpload && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <TextInput
                    label="Drive root"
                    value={form.driveRoot}
                    onChange={on("driveRoot")}
                  />
                  <TextInput
                    label="credentials.json"
                    value={form.driveCredentials}
                    onChange={on("driveCredentials")}
                  />
                  <TextInput
                    label="token.json"
                    value={form.driveToken}
                    onChange={on("driveToken")}
                  />
                  <TextInput
                    label="uploaded.jsonl"
                    value={form.uploadedLog}
                    onChange={on("uploadedLog")}
                  />
                </div>
              )}
            </div>

            <h2 className="text-lg font-semibold mt-6 mb-2">Perfis</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
              <TextInput
                label="Nome do perfil"
                placeholder="meu-site-HLS"
                value={profileName}
                onChange={(e: any) => setProfileName(e.target.value)}
              />
              <button
                onClick={saveProfile}
                className="h-10 rounded-xl bg-slate-900 text-white px-4 hover:bg-slate-800"
              >
                Salvar
              </button>
              <select
                className="h-10 rounded-xl border px-3"
                onChange={(e) => e.target.value && loadProfile(e.target.value)}
              >
                <option value="">Carregar…</option>
                {profiles.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>
            {profiles.length > 0 && (
              <div className="mt-2 text-sm text-slate-600">
                {profiles.map((p) => (
                  <button
                    key={p}
                    onClick={() => deleteProfile(p)}
                    className="mr-2 mt-1 rounded-lg border px-2 py-1 hover:bg-slate-50"
                  >
                    Excluir “{p}”
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="bg-white rounded-2xl shadow p-5 md:p-6">
            <h2 className="text-lg font-semibold mb-3">
              Comando — Python (seu script)
            </h2>
            <CodeBlock code={buildPythonCmd} />
            <div className="mt-2 flex gap-2">
              <button
                onClick={() => copy(buildPythonCmd)}
                className="rounded-xl bg-slate-900 text-white px-4 py-2 hover:bg-slate-800"
              >
                Copiar
              </button>
            </div>

            <h2 className="text-lg font-semibold mt-8 mb-3">
              Comando — yt-dlp (alternativo)
            </h2>
            <CodeBlock code={buildYtDlpCmd} />
            <div className="mt-2 flex gap-2">
              <button
                onClick={() => copy(buildYtDlpCmd)}
                className="rounded-xl bg-slate-900 text-white px-4 py-2 hover:bg-slate-800"
              >
                Copiar
              </button>
            </div>

            <div className="mt-8 text-sm text-slate-600 leading-relaxed">
              <p>Observações:</p>
              <ul className="list-disc ml-5 mt-2 space-y-1">
                <li>
                  Respeite os termos de uso e direitos autorais; não há suporte
                  a DRM.
                </li>
                <li>
                  Para MP4 estrito, ajuste <em>fmt</em> para{" "}
                  <code>
                    bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]
                  </code>
                  .
                </li>
              </ul>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function TextInput({ label, helper, ...rest }: any) {
  return (
    <label className="block">
      <div className="mb-1 text-sm text-slate-700">{label}</div>
      <input
        {...rest}
        className={`w-full h-10 rounded-xl border px-3 outline-none focus:ring-2 focus:ring-slate-300 ${
          rest.readOnly ? "bg-slate-100" : ""
        }`}
      />
      {helper && <div className="mt-1 text-xs text-slate-500">{helper}</div>}
    </label>
  );
}

function NumberInput({
  label,
  value,
  onChange,
  min,
}: {
  label: string;
  value: string;
  onChange: any;
  min?: string;
}) {
  return (
    <label className="block">
      <div className="mb-1 text-sm text-slate-700">{label}</div>
      <input
        type="number"
        min={min || "0"}
        value={value}
        onChange={onChange}
        className="w-full h-10 rounded-xl border px-3 outline-none focus:ring-2 focus:ring-slate-300"
      />
    </label>
  );
}

function Checkbox({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: any;
}) {
  return (
    <label className="flex items-center gap-3 select-none">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="h-4 w-4 rounded border-slate-400"
      />
      <span className="text-slate-800 text-sm">{label}</span>
    </label>
  );
}

function CodeBlock({ code }: { code: string }) {
  return (
    <pre className="rounded-xl bg-slate-900 text-slate-100 p-4 text-xs md:text-sm overflow-x-auto">
      <code>{code}</code>
    </pre>
  );
}
