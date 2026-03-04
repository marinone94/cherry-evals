{{/*
Expand the name of the chart.
*/}}
{{- define "cherry-evals.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this.
*/}}
{{- define "cherry-evals.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart label.
*/}}
{{- define "cherry-evals.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels applied to all resources.
*/}}
{{- define "cherry-evals.labels" -}}
helm.sh/chart: {{ include "cherry-evals.chart" . }}
{{ include "cherry-evals.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels for the API deployment.
*/}}
{{- define "cherry-evals.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cherry-evals.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API component selector labels.
*/}}
{{- define "cherry-evals.api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cherry-evals.name" . }}-api
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Postgres component selector labels.
*/}}
{{- define "cherry-evals.postgres.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cherry-evals.name" . }}-postgres
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: postgres
{{- end }}

{{/*
Qdrant component selector labels.
*/}}
{{- define "cherry-evals.qdrant.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cherry-evals.name" . }}-qdrant
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: qdrant
{{- end }}

{{/*
Create the name of the service account to use.
*/}}
{{- define "cherry-evals.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "cherry-evals.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Build the internal Postgres host name.
*/}}
{{- define "cherry-evals.postgresHost" -}}
{{- printf "%s-postgres" (include "cherry-evals.fullname" .) }}
{{- end }}

{{/*
Build the DATABASE_URL for the API.
Uses internal Postgres when postgres.enabled=true, otherwise externalPostgres.
*/}}
{{- define "cherry-evals.databaseUrl" -}}
{{- if .Values.postgres.enabled }}
{{- printf "postgresql://%s:%s@%s:%d/%s" .Values.postgres.username .Values.postgres.password (include "cherry-evals.postgresHost" .) (int .Values.postgres.port) .Values.postgres.database }}
{{- else }}
{{- printf "postgresql://%s:%s@%s:%d/%s" .Values.externalPostgres.username .Values.externalPostgres.password .Values.externalPostgres.host (int .Values.externalPostgres.port) .Values.externalPostgres.database }}
{{- end }}
{{- end }}

{{/*
Build the QDRANT_URL for the API.
*/}}
{{- define "cherry-evals.qdrantUrl" -}}
{{- if .Values.qdrant.enabled }}
{{- printf "http://%s-qdrant:%d" (include "cherry-evals.fullname" .) (int .Values.qdrant.port) }}
{{- else }}
{{- printf "http://%s:%d" .Values.externalQdrant.host (int .Values.externalQdrant.port) }}
{{- end }}
{{- end }}

{{/*
Name of the secret holding API keys.
*/}}
{{- define "cherry-evals.secretName" -}}
{{- printf "%s-secret" (include "cherry-evals.fullname" .) }}
{{- end }}

{{/*
Name of the ConfigMap holding non-secret config.
*/}}
{{- define "cherry-evals.configMapName" -}}
{{- printf "%s-config" (include "cherry-evals.fullname" .) }}
{{- end }}
