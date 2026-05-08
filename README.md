# Skeleton-User-Interface

人體骨架分析系統，整合 YOLOv11 物件偵測、ViTPose 骨架姿態估計（26 關節點）與 BoTSORT 多目標追蹤，以 PyQt5 GUI 呈現，可對運動影片進行骨架偵測與關節點追蹤。

---

## 目錄

1. [環境需求](#環境需求)
2. [安裝步驟](#安裝步驟)
3. [模型準備](#模型準備)
4. [啟動程式](#啟動程式)
5. [UI 操作說明](#ui-操作說明)
6. [輸出格式](#輸出格式)
7. [攝影機支援](#攝影機支援)
8. [專案結構](#專案結構)
9. [常見問題](#常見問題)

---

## 環境需求

| 項目 | 版本 |
|------|------|
| OS | Windows 10 / 11 |
| Python | 3.8 |
| CUDA | 11.8 |
| cuDNN | 對應 CUDA 11.8 |
| Anaconda | 任意版本 |

> GPU 為必要條件，CPU-only 模式未支援。

---

## 安裝步驟

> **注意**：所有指令請在 **Anaconda Prompt** 或已初始化 conda 的 PowerShell 中執行。
> PowerShell 需先執行 `conda init powershell` 並重新開啟視窗，才能使用 `conda activate`。

---

### Step 1 — 建立 Conda 環境

```bash
conda create -n Skeleton python=3.8 -y
conda activate Skeleton
```

---

### Step 2 — 安裝 PyTorch（CUDA 11.8）

```bash
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
```

---

### Step 3 — 安裝基本套件

```bash
pip install -r requirements.txt
```

---

### Step 4 — 安裝 PyQt5

```bash
pip install PyQt5==5.15.11
```

---

### Step 5 — 安裝 OpenMMLab 套件

```bash
pip install -U openmim
mim install "mmcv==2.0.0"
mim install "mmdet==3.1.0"
mim install mmengine
```

---

### Step 6 — 安裝 mmpose（從本專案原始碼）

Windows 上 `.mim` 資料夾有權限問題，**必須先刪除再安裝**：

```powershell
# 回到專案根目錄（若不在根目錄請先 cd 過去）
cd C:\Mo\program\Hitter-Skeleton-User-Interface_zm

# 刪除 .mim 資料夾（若不存在會顯示錯誤可忽略）
Remove-Item -Recurse -Force Src\mmpose_main\mmpose\.mim

# 安裝
cd Src\mmpose_main
python setup.py develop --no-deps
cd ..\..
```

---

### Step 7 — 安裝 mmpretrain（從本專案原始碼）

ViTPose 的 Vision Transformer backbone 需要此套件，同樣需先刪除 `.mim`：

```powershell
# 回到專案根目錄
cd C:\Mo\program\Hitter-Skeleton-User-Interface_zm

# 刪除 .mim 資料夾（若不存在會顯示錯誤可忽略）
Remove-Item -Recurse -Force Src\mmpretrain_main\mmpretrain\.mim

# 安裝
cd Src\mmpretrain_main
python setup.py develop --no-deps
cd ..\..
```

---

### Step 8 — 安裝 faiss 與 cython_bbox

```bash
conda install -c conda-forge faiss-gpu -y
pip install cython_bbox
```

---

### Step 9 — 驗證安裝

執行以下指令，確認所有關鍵套件正常：

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# 應輸出: 2.0.1+cu118 True

python -c "import mmpose; print(mmpose.__version__)"
# 應輸出: 1.3.1

python -c "import mmpretrain; print(mmpretrain.__version__)"
# 應輸出: 1.2.0

python -c "from ultralytics import YOLO; print('YOLO OK')"
# 應輸出: YOLO OK
```

> **libiomp5md.dll 衝突**：若出現 OpenMP 相關警告，請刪除：
> `C:\Users\<你的帳號>\anaconda3\envs\Skeleton\Library\bin\libiomp5md.dll`

---

## 模型準備

將以下模型檔案放至 `Db/pretrain/` 資料夾（請向專案負責人索取 Google Drive 連結）：

| 檔案名稱 | 用途 | 大小（約）|
|---------|------|---------|
| `epoch_210.pth` | ViTPose 姿態估計模型（HALPE 26 關節點） | ~1.1 GB |
| `yolo11m-seg.pt` | YOLOv11 人體偵測模型 | ~45 MB |

下載後目錄結構應如下：

```
Hitter-Skeleton-User-Interface/
├── Db/
│   ├── pretrain/
│   │   ├── epoch_210.pth        ← ViTPose 模型
│   │   └── yolo11m-seg.pt       ← YOLOv11 模型
│   └── Record/                  ← 輸出資料夾（自動建立）
└── Src/
```

---

## 啟動程式

```bash
conda activate Skeleton
cd Src\UI_Control
python main.py
```

---

## UI 操作說明

### 介面總覽

```
┌─────────────────────────────────────┬──────────────────────────┐
│                                     │  2D 關節點               │
│                                     │  ┌──────────────────┐    │
│                                     │  │  檔案            │    │
│         影片顯示區                   │  │  檔名: xxx       │    │
│         (FrameView)                 │  │  FPS: 280        │    │
│                                     │  │ [載入原始影片]    │    │
│                                     │  │ [處理和儲存]      │    │
│                                     │  │ [載入處理過的影片] │    │
│                                     │  └──────────────────┘    │
│                                     │                          │
│                                     │  顯示資訊                │
│                                     │  ☑ 人體骨架  □ 人物框    │
│                                     │  □ 選擇人                │
├─────────────────────────────────────┤                          │
│  [<<]  [▶]  [>>]   ────────●────   │                          │
│                      394 / 580      │                          │
└─────────────────────────────────────┴──────────────────────────┘
```

---

### 按鈕與功能說明

#### 檔案區

| 按鈕 | 功能 |
|------|------|
| **載入原始影片** | 開啟檔案選擇對話框，載入未處理的 MP4 影片。影片載入後會自動逐幀解析並顯示第 0 幀。 |
| **處理和儲存** | 從第 0 幀開始執行骨架偵測，播放完畢後自動將結果儲存為骨架影片（`_skeleton.mp4`）與 JSON 資料到 `Db/Record/`。 |
| **載入處理過的影片** | 載入已處理完成的影片，並同時讀取對應的 JSON 骨架資料，直接顯示骨架結果，不需重新計算。 |

#### 播放控制區

| 按鈕 | 功能 |
|------|------|
| **`<<`** | 退回上一幀 |
| **`▶` / `\|\|`** | 播放 / 暫停 |
| **`>>`** | 前進下一幀 |
| **進度條（Slider）** | 拖曳跳至任意幀，每移動一格就會觸發該幀的骨架偵測 |

> **鍵盤快捷鍵**：按住 `A` 退後一幀，按 `D` 前進一幀（需視窗取得焦點）。

#### 顯示資訊區（Checkbox）

| Checkbox | 功能 |
|----------|------|
| **人體骨架** | 顯示 / 隱藏骨架連線（橘色 = 右側，藍色 = 左側） |
| **人物框** | 顯示 / 隱藏 YOLO 偵測到的人體 Bounding Box |
| **選擇人** | 勾選後，點擊畫面中的人物可選定追蹤目標（鎖定 Person ID） |

---

### 操作流程：對影片進行骨架偵測

以下為完整的操作步驟（以跑步影片為例）：

**① 載入影片**

點擊「**載入原始影片**」→ 在對話框中選擇 MP4 影片 → 等待讀取完成（上方會顯示檔案名稱與解析度）。

**② 開始偵測**

點擊「**處理和儲存**」→ 程式會自動從第 0 幀開始播放並逐幀進行骨架偵測。

> 偵測中可以看到畫面上陸續出現骨架，右上角顯示 FPS 資訊。偵測速度取決於 GPU 效能與影片解析度。

**③ 選取追蹤目標（選擇人）**

1. 確認「**人體骨架**」已勾選
2. 勾選「**選擇人**」
3. 用滑鼠左鍵點擊畫面中想追蹤的運動員

> 選定後，該人物的骨架會被鎖定追蹤，Person ID 固定不變。

**④ 儲存結果**

- 影片播放到最後一幀時自動儲存，或點擊「**處理和儲存**」手動觸發
- 輸出檔案儲存至 `Db/Record/` 資料夾

**⑤ 載入已處理的影片（下次快速開啟）**

下次開啟相同影片時，點擊「**載入處理過的影片**」，程式會自動讀取 JSON 骨架資料，直接顯示結果，不需重新偵測。

---

### 骨架關節點對照（HALPE 26 點）

| ID | 部位 | ID | 部位 |
|----|------|----|------|
| 0 | 鼻子 | 13 | 左膝 |
| 1 | 左眼 | 14 | 右膝 |
| 2 | 右眼 | 15 | 左踝 |
| 3 | 左耳 | 16 | 右踝 |
| 4 | 右耳 | 17 | 頭部 |
| 5 | 左肩 | 18 | 頸部 |
| 6 | 右肩 | 19 | 臀部 |
| 7 | 左肘 | 20 | 左大腳趾 |
| 8 | 右肘 | 21 | 右大腳趾 |
| 9 | 左腕 | 22 | 左小腳趾 |
| 10 | 右腕 | 23 | 右小腳趾 |
| 11 | 左髖 | 24 | 左腳跟 |
| 12 | 右髖 | 25 | 右腳跟 |

---

## 輸出格式

分析完成後，結果儲存至 `Db/Record/`：

| 檔案 | 說明 |
|------|------|
| `{影片名稱}_skeleton.mp4` | 畫有骨架的影片 |
| `{影片名稱}.json` | 逐幀骨架資料（含 Bounding Box + 26 關節點座標） |

JSON 格式範例：
```json
{
  "frame_0": {
    "persons": [
      {
        "person_id": 1,
        "bbox": [x1, y1, x2, y2],
        "keypoints": [
          [x, y, confidence],
          "..."
        ]
      }
    ]
  }
}
```

---

## 攝影機支援

| 攝影機類型 | 狀態 | 說明 |
|-----------|------|------|
| 影片檔（MP4 等）| ✅ 支援 | 主要使用方式 |
| FLIR / Point Grey 工業相機 | ⚠️ 需額外安裝 | 需安裝 [Spinnaker SDK](https://www.flir.com/products/spinnaker-sdk/) + `EasyPySpin` |
| Sony AX700 / 一般相機（HDMI 擷取卡）| 🔧 規劃中 | 透過 `cv2.VideoCapture()` 讀取，需新增 `SonyCaptureThread` |

---

## 專案結構

```
Hitter-Skeleton-User-Interface/
├── Db/
│   ├── pretrain/              # 模型權重檔
│   └── Record/                # 分析輸出（自動建立）
├── Src/
│   ├── UI_Control/            # 主程式
│   │   ├── main.py            # 入口點
│   │   ├── video_widget.py    # 影片分析 Tab 邏輯
│   │   ├── ui/                # PyQt5 UI 定義（.py + .ui）
│   │   ├── skeleton/          # 骨架偵測核心（ViTPose + YOLO + tracker）
│   │   ├── cv_utils/          # 影像控制與執行緒
│   │   ├── utils/             # 分析、濾波、視覺化工具
│   │   └── camera_objects/    # 攝影機介面（擴充用）
│   ├── mmpose_main/           # OpenMMLab mmpose（本地版本，editable 安裝）
│   ├── mmyolo_main/           # OpenMMLab mmyolo
│   ├── tracker/               # BoTSORT 多目標追蹤器
│   └── cython-bbox/           # Bounding Box 計算工具
├── requirements.txt           # Python 套件依賴清單
├── CLAUDE.md                  # 開發環境紀錄（給 Claude Code 使用）
└── README.md                  # 本文件
```

---

## 常見問題

**Q：程式啟動時出現 `ModuleNotFoundError: No module named 'mmpose'`**

A：mmpose 需從本專案原始碼安裝。執行：
```bash
conda activate Skeleton
cd Src\mmpose_main
python setup.py develop --no-deps
```
若出現 `PermissionError [WinError 5]`，先刪除 `Src\mmpose_main\mmpose\.mim` 資料夾。

---

**Q：程式啟動時出現 `ModuleNotFoundError: No module named 'ultralytics'`**

A：執行：
```bash
conda activate Skeleton
pip install ultralytics==8.3.96
```

---

**Q：出現 `EasyPySpin` 相關錯誤**

A：`EasyPySpin` 是 FLIR 工業相機的 SDK，非必要套件，已透過 `try/except` 處理。若仍出錯，代表程式碼有未預期的路徑直接使用它，請回報 issue。

---

**Q：出現 `libiomp5md.dll` 衝突警告**

A：刪除 `C:\Users\<帳號>\anaconda3\envs\Skeleton\Library\bin\libiomp5md.dll` 即可解決。

---

**Q：影片偵測速度很慢**

A：確認 `torch.cuda.is_available()` 回傳 `True`。若為 `False`，代表 PyTorch 使用 CPU 模式，需重新安裝 CUDA 版本的 PyTorch（見 Step 2）。

---

**Q：到另一台電腦安裝時，mmpose setup.py 失敗**

A：常見原因是 `.mim` 資料夾的 Windows 權限問題。步驟：
1. 手動刪除 `Src\mmpose_main\mmpose\.mim`
2. 再次執行 `python setup.py develop --no-deps`
