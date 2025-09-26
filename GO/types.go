package main

type ConnectionParams struct {
	Driver   string `json:"driver"`
	Server   string `json:"server"`
	Name     string `json:"name"`
	User     string `json:"user"`
	Password string `json:"password"`
}

type QueryNode struct {
	Connector string                   `json:"connector"`
	Children  []map[string]interface{} `json:"children"`
}

type Request struct {
	Operation    string                 `json:"operation"`
	Table        string                 `json:"table,omitempty"`
	Fields       []string               `json:"fields,omitempty"`
	Data         map[string]interface{} `json:"data,omitempty"`
	WhereQ       QueryNode              `json:"where_q,omitempty"`
	Driver       string                 `json:"driver,omitempty"`
	SQL          string                 `json:"sql,omitempty"`
	Params       []interface{}          `json:"params,omitempty"`
	ExpectResult bool                   `json:"expect_result,omitempty"`
}
