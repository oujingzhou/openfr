/**
 * Tool discovery: fetch tool metadata from the Python server
 * and convert JSON Schema parameters to TypeBox schemas.
 */

import { Type, type TSchema, type TObject } from "@sinclair/typebox";

// ---------------------------------------------------------------------------
// Types returned by the Python /tools endpoint
// ---------------------------------------------------------------------------

export interface ToolMeta {
  name: string;
  description: string;
  label: string;
  category: string;
  parameters: Record<string, unknown>; // JSON Schema
}

// ---------------------------------------------------------------------------
// Fetch tools from the Python server
// ---------------------------------------------------------------------------

export async function discoverTools(
  serverUrl: string,
  signal?: AbortSignal,
): Promise<ToolMeta[]> {
  const url = `${serverUrl.replace(/\/+$/, "")}/tools`;
  const res = await fetch(url, { signal });

  if (!res.ok) {
    throw new Error(`Tool discovery failed: ${res.status} ${res.statusText}`);
  }

  const data = (await res.json()) as { tools: ToolMeta[] };
  return data.tools;
}

// ---------------------------------------------------------------------------
// JSON Schema → TypeBox conversion (simplified)
// ---------------------------------------------------------------------------

/**
 * Convert a JSON Schema object (from Pydantic) into a TypeBox TSchema.
 *
 * We support the subset used by LangChain tool args_schema:
 * - object with properties (string, number, integer, boolean, array)
 * - required fields
 * - description annotations
 */
export function jsonSchemaToTypebox(schema: Record<string, unknown>): TSchema {
  const type = schema.type as string | undefined;

  if (type === "object" || schema.properties) {
    return jsonSchemaObjectToTypebox(schema);
  }
  if (type === "string") {
    const opts: Record<string, unknown> = {};
    if (schema.description) opts.description = schema.description;
    if (schema.default !== undefined) opts.default = schema.default;
    if (schema.enum) return Type.Union((schema.enum as string[]).map((v) => Type.Literal(v)), opts);
    return Type.String(opts);
  }
  if (type === "number" || type === "integer") {
    const opts: Record<string, unknown> = {};
    if (schema.description) opts.description = schema.description;
    if (schema.default !== undefined) opts.default = schema.default;
    return type === "integer" ? Type.Integer(opts) : Type.Number(opts);
  }
  if (type === "boolean") {
    const opts: Record<string, unknown> = {};
    if (schema.description) opts.description = schema.description;
    return Type.Boolean(opts);
  }
  if (type === "array") {
    const items = (schema.items as Record<string, unknown>) ?? {};
    const opts: Record<string, unknown> = {};
    if (schema.description) opts.description = schema.description;
    return Type.Array(jsonSchemaToTypebox(items), opts);
  }

  // Fallback: accept anything
  return Type.Any();
}

function jsonSchemaObjectToTypebox(schema: Record<string, unknown>): TObject {
  const properties = (schema.properties ?? {}) as Record<string, Record<string, unknown>>;
  const required = new Set((schema.required ?? []) as string[]);

  const tbProps: Record<string, TSchema> = {};
  for (const [key, propSchema] of Object.entries(properties)) {
    let tbProp = jsonSchemaToTypebox(propSchema);
    if (!required.has(key)) {
      tbProp = Type.Optional(tbProp);
    }
    tbProps[key] = tbProp;
  }

  return Type.Object(tbProps);
}
