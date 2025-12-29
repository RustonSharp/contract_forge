# 合同文件管理 API

提供合同文件的上传、查询等功能，文件按日期自动组织存储。

## 文件存储规则

文件会自动保存到 `uploads/YYYY-MM-DD/` 目录下，按日期组织：
- 2025年11月12日上传的文件 → `uploads/2025-11-12/`
- 2025年11月13日上传的文件 → `uploads/2025-11-13/`

如果同一天上传同名文件，会自动添加 UUID 前缀避免覆盖。

## 接口说明

### 1. 上传文件

**POST** `/api/files/upload`

上传合同文件。

**请求**：
- Content-Type: `multipart/form-data`
- 参数：`file` (文件)

**响应**：
```json
{
    "success": true,
    "message": "文件上传成功",
    "file_info": {
        "file_name": "test_contract.pdf",
        "file_path": "2025-11-12/test_contract.pdf",
        "file_size": 32768,
        "upload_date": "2025-11-12",
        "file_type": ".pdf"
    }
}
```

**支持的文件类型**：
- `.pdf` - PDF 文档
- `.docx`, `.doc` - Word 文档
- `.jpg`, `.jpeg`, `.png` - 图片文件

### 2. 查询文件列表

**GET** `/api/files/list`

查询已上传的文件列表，支持按日期筛选和分页。

**查询参数**：
- `date` (可选): 日期筛选，格式 `YYYY-MM-DD`，如 `2025-11-12`
- `page` (可选): 页码，从1开始，默认 1
- `page_size` (可选): 每页数量，默认 20，最大 100

**响应**：
```json
{
    "success": true,
    "total": 10,
    "files": [
        {
            "file_name": "test_contract.pdf",
            "file_path": "2025-11-12/test_contract.pdf",
            "file_size": 32768,
            "upload_date": "2025-11-12",
            "file_type": ".pdf"
        }
    ],
    "date": "2025-11-12"
}
```

### 3. 获取所有日期列表

**GET** `/api/files/list/dates`

获取所有有文件的日期列表（用于筛选）。

**响应**：
```json
{
    "success": true,
    "dates": [
        "2025-11-13",
        "2025-11-12",
        "2025-11-11"
    ],
    "total": 3
}
```

### 4. 获取文件信息

**GET** `/api/files/info/{file_name}`

获取指定文件的详细信息。

**路径参数**：
- `file_name`: 文件名（可以是完整文件名或部分文件名）

**响应**：
```json
{
    "file_name": "test_contract.pdf",
    "file_path": "2025-11-12/test_contract.pdf",
    "file_size": 32768,
    "upload_date": "2025-11-12",
    "file_type": ".pdf"
}
```

## 使用示例

### Python 示例

```python
import requests

# 上传文件
with open("contract.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/files/upload",
        files={"file": f}
    )
    print(response.json())

# 查询文件列表
response = requests.get(
    "http://localhost:8000/api/files/list",
    params={"date": "2025-11-12", "page": 1, "page_size": 20}
)
print(response.json())

# 获取所有日期
response = requests.get("http://localhost:8000/api/files/list/dates")
print(response.json())
```

### cURL 示例

```bash
# 上传文件
curl -X POST "http://localhost:8000/api/files/upload" \
  -F "file=@contract.pdf"

# 查询文件列表（按日期）
curl "http://localhost:8000/api/files/list?date=2025-11-12&page=1&page_size=20"

# 查询所有文件
curl "http://localhost:8000/api/files/list?page=1&page_size=20"

# 获取所有日期
curl "http://localhost:8000/api/files/list/dates"
```

## 文件路径说明

- **相对路径**：`2025-11-12/test_contract.pdf`（相对于 uploads 目录）
- **绝对路径**：`/path/to/project/uploads/2025-11-12/test_contract.pdf`

在调用其他工具（如文档解析工具）时，可以使用相对路径或完整路径。

