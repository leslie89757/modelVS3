-- 清理现有工具（如果需要）
TRUNCATE TABLE tools RESTART IDENTITY CASCADE;

-- 1. 精确时间工具
INSERT INTO tools (id, name, description, schema, enabled, created_at, updated_at) VALUES (
    gen_random_uuid(),
    'precision_time',
    '获取当前精确时间，支持多种时区和格式化选项',
    '{
        "type": "function",
        "function": {
            "name": "precision_time",
            "description": "获取当前精确时间，支持多种时区和格式化选项",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "时区名称，如 UTC, Asia/Shanghai, America/New_York",
                        "default": "UTC"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["iso", "timestamp", "human", "custom"],
                        "description": "时间格式",
                        "default": "iso"
                    },
                    "custom_format": {
                        "type": "string",
                        "description": "自定义时间格式（当format为custom时使用）"
                    },
                    "locale": {
                        "type": "string",
                        "description": "语言环境，如 zh_CN, en_US",
                        "default": "zh_CN"
                    },
                    "include_milliseconds": {
                        "type": "boolean",
                        "description": "是否包含毫秒",
                        "default": false
                    }
                },
                "required": []
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);

-- 2. 万年历工具
INSERT INTO tools (id, name, description, schema, enabled, created_at, updated_at) VALUES (
    gen_random_uuid(),
    'calendar',
    '万年历工具，提供日期查询、农历转换、节日查询、年龄计算等功能',
    '{
        "type": "function",
        "function": {
            "name": "calendar",
            "description": "万年历工具，提供日期查询、农历转换、节日查询、年龄计算等功能",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get_date_info", "get_month_calendar", "get_year_info", "calculate_age"],
                        "description": "操作类型",
                        "default": "get_date_info"
                    },
                    "year": {
                        "type": "integer",
                        "description": "年份 (1900-2100)",
                        "minimum": 1900,
                        "maximum": 2100
                    },
                    "month": {
                        "type": "integer",
                        "description": "月份 (1-12)",
                        "minimum": 1,
                        "maximum": 12
                    },
                    "day": {
                        "type": "integer",
                        "description": "日期 (1-31)",
                        "minimum": 1,
                        "maximum": 31
                    },
                    "birth_year": {
                        "type": "integer",
                        "description": "出生年份（用于年龄计算）"
                    },
                    "birth_month": {
                        "type": "integer",
                        "description": "出生月份（用于年龄计算）"
                    },
                    "birth_day": {
                        "type": "integer",
                        "description": "出生日期（用于年龄计算）"
                    },
                    "include_lunar": {
                        "type": "boolean",
                        "description": "是否包含农历信息",
                        "default": true
                    },
                    "include_festivals": {
                        "type": "boolean",
                        "description": "是否包含节日信息",
                        "default": true
                    },
                    "include_zodiac": {
                        "type": "boolean",
                        "description": "是否包含生肖星座信息",
                        "default": true
                    },
                    "locale": {
                        "type": "string",
                        "description": "语言环境",
                        "default": "zh_CN"
                    }
                },
                "required": ["action"]
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);

-- 3. 奇门遁甲工具
INSERT INTO tools (id, name, description, schema, enabled, created_at, updated_at) VALUES (
    gen_random_uuid(),
    'qimen_dunjia',
    '奇门遁甲起盘工具，可以根据指定时间起奇门局进行预测分析',
    '{
        "type": "function",
        "function": {
            "name": "qimen_dunjia",
            "description": "奇门遁甲起盘工具，可以根据指定时间起奇门局进行预测分析",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "年份",
                        "minimum": 1900,
                        "maximum": 2100
                    },
                    "month": {
                        "type": "integer",
                        "description": "月份 (1-12)",
                        "minimum": 1,
                        "maximum": 12
                    },
                    "day": {
                        "type": "integer",
                        "description": "日期 (1-31)",
                        "minimum": 1,
                        "maximum": 31
                    },
                    "hour": {
                        "type": "integer",
                        "description": "小时 (0-23)",
                        "minimum": 0,
                        "maximum": 23
                    },
                    "minute": {
                        "type": "integer",
                        "description": "分钟 (0-59)",
                        "minimum": 0,
                        "maximum": 59,
                        "default": 0
                    },
                    "question": {
                        "type": "string",
                        "description": "要问的问题或求测的事项"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["转盘", "飞盘"],
                        "description": "起盘方法",
                        "default": "转盘"
                    },
                    "include_analysis": {
                        "type": "boolean",
                        "description": "是否包含分析解释",
                        "default": true
                    }
                },
                "required": ["year", "month", "day", "hour"]
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);

-- 4. 网络搜索工具
INSERT INTO tools (id, name, description, schema, enabled, created_at, updated_at) VALUES (
    gen_random_uuid(),
    'web_search',
    '在互联网上搜索信息，获取最新的网络内容',
    '{
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "在互联网上搜索信息，获取最新的网络内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询关键词"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "返回结果数量，最多10个",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    },
                    "language": {
                        "type": "string",
                        "description": "搜索语言",
                        "default": "zh-CN"
                    },
                    "region": {
                        "type": "string",
                        "description": "搜索地区",
                        "default": "CN"
                    }
                },
                "required": ["query"]
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);

-- 5. 计算器工具
INSERT INTO tools (id, name, description, schema, enabled, created_at, updated_at) VALUES (
    gen_random_uuid(),
    'calculator',
    '执行数学计算，支持基本运算、函数运算和复杂表达式',
    '{
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "执行数学计算，支持基本运算、函数运算和复杂表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，如 \"2+3*4\", \"sin(0.5)\", \"sqrt(16)\""
                    },
                    "precision": {
                        "type": "integer",
                        "description": "小数点精度",
                        "minimum": 0,
                        "maximum": 10,
                        "default": 4
                    }
                },
                "required": ["expression"]
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);

-- 6. 文件读取工具
INSERT INTO tools (id, name, description, schema, enabled, created_at, updated_at) VALUES (
    gen_random_uuid(),
    'file_reader',
    '读取和分析文件内容，支持多种文件格式',
    '{
        "type": "function",
        "function": {
            "name": "file_reader",
            "description": "读取和分析文件内容，支持多种文件格式",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "文件编码",
                        "default": "utf-8"
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "最大读取行数",
                        "default": 1000
                    },
                    "format": {
                        "type": "string",
                        "enum": ["text", "json", "csv", "auto"],
                        "description": "文件格式",
                        "default": "auto"
                    }
                },
                "required": ["file_path"]
            }
        }
    }'::jsonb,
    true,
    NOW(),
    NOW()
);

-- 显示注册结果
SELECT name, description, enabled FROM tools ORDER BY name; 