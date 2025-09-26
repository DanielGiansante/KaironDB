# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with 66 tests
- Robust exception hierarchy with context-rich error messages
- Professional logging system replacing DebugLogger
- Type hints and improved code organization
- Makefile for common development tasks
- Requirements files for dependencies management

### Changed
- Improved model inheritance system
- Enhanced parameter validation with detailed error messages
- Better cleanup handling in SQLBridge destructor
- Reorganized project structure for better maintainability

### Fixed
- Fixed model attribute access returning field objects instead of values
- Fixed inheritance not collecting fields from base classes
- Fixed cleanup warnings in destructor
- Fixed import issues in build system

## [1.0.1] - 2024-09-26

### Added
- Initial release of KaironDB
- Async Python ORM with Go backend
- Support for PostgreSQL, SQL Server, MySQL, and SQLite
- Declarative model system with validation
- Q objects for complex queries
- Transaction support
- Connection pooling

### Features
- Truly asynchronous database operations
- High performance through Go DLL backend
- Multi-database support
- Declarative model definitions
- Complex query building with Q objects
- Atomic transactions
- Connection pooling
