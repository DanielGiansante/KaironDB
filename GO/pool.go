package main

import (
	"database/sql"
	"fmt"
	"sync"

	"github.com/google/uuid"
)

type poolManager struct {
	pools map[string]*sql.DB
	mu    sync.RWMutex
}

var globalPoolManager = &poolManager{
	pools: make(map[string]*sql.DB),
}

func (pm *poolManager) Create(params ConnectionParams) (string, error) {
	db, err := connect(params)
	if err != nil {
		return "", err
	}
	if err := db.Ping(); err != nil {
		db.Close()
		return "", fmt.Errorf("falha ao conectar ao banco de dados: %w", err)
	}
	pm.mu.Lock()
	defer pm.mu.Unlock()
	poolID := uuid.New().String()
	pm.pools[poolID] = db
	return poolID, nil
}

func (pm *poolManager) Get(poolID string) (*sql.DB, bool) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()
	pool, found := pm.pools[poolID]
	return pool, found
}

func (pm *poolManager) Close(poolID string) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()
	pool, found := pm.pools[poolID]
	if !found {
		return fmt.Errorf("pool com ID %s não encontrado", poolID)
	}
	delete(pm.pools, poolID)
	return pool.Close()
}
