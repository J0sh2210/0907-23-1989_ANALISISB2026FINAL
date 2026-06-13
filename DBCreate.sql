CREATE DATABASE NetworkIncidentsDB;
GO
USE NetworkIncidentsDB;
GO

-- Catálogos básicos
CREATE TABLE Specialties (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL
);

CREATE TABLE Severities (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(50) NOT NULL, -- Ej: Baja, Media, Alta, Urgente, Crítico
    MaxResolutionHours INT NOT NULL -- Regla 1: Tiempo de resolución depende de severidad
);

CREATE TABLE IncidentTypes (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    SpecialtyId INT NOT NULL FOREIGN KEY REFERENCES Specialties(Id)
);

CREATE TABLE Technicians (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    SpecialtyId INT NOT NULL FOREIGN KEY REFERENCES Specialties(Id)
);

-- Tabla principal de incidentes
CREATE TABLE Incidents (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Title NVARCHAR(200) NOT NULL,
    Description NVARCHAR(MAX),
    Status NVARCHAR(50) NOT NULL DEFAULT 'Registrado', -- Registrado, Asignado, En progreso, Resuelto, Cerrado, Escalado
    SeverityId INT NOT NULL FOREIGN KEY REFERENCES Severities(Id),
    TypeId INT NOT NULL FOREIGN KEY REFERENCES IncidentTypes(Id),
    TechnicianId INT NULL FOREIGN KEY REFERENCES Technicians(Id),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE()
);

-- Regla 7: Historial / Bitácora de cambios de estado
CREATE TABLE IncidentHistory (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    IncidentId INT NOT NULL FOREIGN KEY REFERENCES Incidents(Id),
    OldStatus NVARCHAR(50) NULL,
    NewStatus NVARCHAR(50) NOT NULL,
    ChangedAt DATETIME DEFAULT GETDATE(),
    ChangedBy NVARCHAR(100) NULL,
    Notes NVARCHAR(MAX) NULL
);