package main

import (
	"database/sql"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func buildRouter(db *sql.DB, cfg Config) *chi.Mux {
	r := chi.NewRouter()
	r.Use(
		middleware.RequestID,
		middleware.RealIP,
		middleware.Logger,
		middleware.Recoverer,
		middleware.Timeout(5*time.Second),
	)

	r.Get("/health", healthHandler(db))
	r.Get("/recommendations", recommendationsHandler(db, cfg))

	return r
}
