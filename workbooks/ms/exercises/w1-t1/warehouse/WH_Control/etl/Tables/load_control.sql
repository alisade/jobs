-- Database project: WH_Control (Fabric Warehouse). Table: etl.load_control
-- Changed in PR #412 "refactor: move control table from Azure SQL to Fabric Warehouse".
-- Column names were aligned with the enterprise naming standard (source_* / target_*).
CREATE TABLE [etl].[load_control]
(
    [load_id]          INT            NOT NULL,
    [source_system]    VARCHAR(20)    NOT NULL,
    [source_schema]    VARCHAR(128)   NOT NULL,
    [source_table]     VARCHAR(128)   NOT NULL,
    [target_table]     VARCHAR(128)   NOT NULL,
    [watermark_column] VARCHAR(128)   NOT NULL,
    [last_watermark]   DATETIME2(3)   NOT NULL,
    [is_enabled]       BIT            NOT NULL
);
GO
