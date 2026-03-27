-- Script SQL de création de la base de données attrition_db
-- Alternative au script Python init_db.py

-- Création de la base de données
CREATE DATABASE attrition_db;

-- Connexion à la base
\c attrition_db;

-- Table des employés (dataset complet)
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    age INTEGER NOT NULL,
    genre VARCHAR(10) NOT NULL,
    revenu_mensuel INTEGER NOT NULL,
    statut_marital VARCHAR(50) NOT NULL,
    departement VARCHAR(50) NOT NULL,
    poste VARCHAR(100) NOT NULL,
    nombre_experiences_precedentes INTEGER NOT NULL,
    annee_experience_totale INTEGER NOT NULL,
    annees_dans_l_entreprise INTEGER NOT NULL,
    annees_dans_le_poste_actuel INTEGER NOT NULL,
    satisfaction_employee_environnement INTEGER NOT NULL CHECK (satisfaction_employee_environnement BETWEEN 1 AND 4),
    note_evaluation_precedente INTEGER NOT NULL CHECK (note_evaluation_precedente BETWEEN 1 AND 4),
    niveau_hierarchique_poste INTEGER NOT NULL CHECK (niveau_hierarchique_poste BETWEEN 1 AND 5),
    satisfaction_employee_nature_travail INTEGER NOT NULL CHECK (satisfaction_employee_nature_travail BETWEEN 1 AND 4),
    satisfaction_employee_equipe INTEGER NOT NULL CHECK (satisfaction_employee_equipe BETWEEN 1 AND 4),
    satisfaction_employee_equilibre_pro_perso INTEGER NOT NULL CHECK (satisfaction_employee_equilibre_pro_perso BETWEEN 1 AND 4),
    note_evaluation_actuelle INTEGER NOT NULL,
    heure_supplementaires VARCHAR(10) NOT NULL,
    augementation_salaire_precedente VARCHAR(10) NOT NULL,
    nombre_participation_pee INTEGER NOT NULL,
    nb_formations_suivies INTEGER NOT NULL,
    distance_domicile_travail INTEGER NOT NULL,
    niveau_education INTEGER NOT NULL CHECK (niveau_education BETWEEN 1 AND 5),
    domaine_etude VARCHAR(100) NOT NULL,
    frequence_deplacement VARCHAR(50) NOT NULL,
    annees_depuis_la_derniere_promotion INTEGER NOT NULL,
    annes_sous_responsable_actuel INTEGER NOT NULL,
    a_quitte_l_entreprise VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table de log des prédictions
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    input_data JSONB NOT NULL,
    prediction INTEGER NOT NULL CHECK (prediction IN (0, 1)),
    probability FLOAT NOT NULL CHECK (probability BETWEEN 0 AND 1),
    model_version VARCHAR(50) DEFAULT '1.0.0',
    api_key_used VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table de gestion des clés API
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour les requêtes fréquentes
CREATE INDEX idx_predictions_created_at ON predictions (created_at DESC);
CREATE INDEX idx_api_keys_hash ON api_keys (key_hash) WHERE is_active = TRUE;
CREATE INDEX idx_employees_departement ON employees (departement);
