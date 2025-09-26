package main

import (
	"database/sql"
	"fmt"
	"sync"

	"github.com/google/uuid"
)

type transactionEntry struct {
	tx *sql.Tx
}

type transactionManager struct {
	transactions map[string]transactionEntry
	mu           sync.RWMutex
}

var txManager = &transactionManager{
	transactions: make(map[string]transactionEntry),
}

func (tm *transactionManager) Begin(db *sql.DB) (string, error) {
	tx, err := db.Begin()
	if err != nil {
		return "", err
	}
	tm.mu.Lock()
	defer tm.mu.Unlock()
	txID := uuid.New().String()
	tm.transactions[txID] = transactionEntry{tx: tx}
	return txID, nil
}

func (tm *transactionManager) Get(txID string) (transactionEntry, bool) {
	tm.mu.RLock()
	defer tm.mu.RUnlock()
	entry, found := tm.transactions[txID]
	return entry, found
}

func (tm *transactionManager) Commit(txID string) error {
	tm.mu.Lock()
	defer tm.mu.Unlock()
	entry, found := tm.transactions[txID]
	if !found {
		return fmt.Errorf("transação com ID %s não encontrada", txID)
	}
	delete(tm.transactions, txID)
	return entry.tx.Commit()
}

func (tm *transactionManager) Rollback(txID string) error {
	tm.mu.Lock()
	defer tm.mu.Unlock()
	entry, found := tm.transactions[txID]
	if !found {
		return fmt.Errorf("transação com ID %s não encontrada", txID)
	}
	delete(tm.transactions, txID)
	return entry.tx.Rollback()
}
