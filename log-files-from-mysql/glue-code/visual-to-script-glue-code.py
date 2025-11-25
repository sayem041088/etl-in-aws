import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.gluetypes import *
from awsgluedq.transforms import EvaluateDataQuality
from awsglue import DynamicFrame
import re


def _find_null_fields(ctx, schema, path, output, nullStringSet, nullIntegerSet, frame):
    if isinstance(schema, StructType):
        for field in schema:
            new_path = path + "." if path != "" else path
            output = _find_null_fields(
                ctx,
                field.dataType,
                new_path + field.name,
                output,
                nullStringSet,
                nullIntegerSet,
                frame,
            )
    elif isinstance(schema, ArrayType):
        if isinstance(schema.elementType, StructType):
            output = _find_null_fields(
                ctx,
                schema.elementType,
                path,
                output,
                nullStringSet,
                nullIntegerSet,
                frame,
            )
    elif isinstance(schema, NullType):
        output.append(path)
    else:
        x, distinct_set = frame.toDF(), set()
        for i in x.select(path).distinct().collect():
            distinct_ = i[path.split(".")[-1]]
            if isinstance(distinct_, list):
                distinct_set |= set(
                    [
                        item.strip() if isinstance(item, str) else item
                        for item in distinct_
                    ]
                )
            elif isinstance(distinct_, str):
                distinct_set.add(distinct_.strip())
            else:
                distinct_set.add(distinct_)
        if isinstance(schema, StringType):
            if distinct_set.issubset(nullStringSet):
                output.append(path)
        elif (
            isinstance(schema, IntegerType)
            or isinstance(schema, LongType)
            or isinstance(schema, DoubleType)
        ):
            if distinct_set.issubset(nullIntegerSet):
                output.append(path)
    return output


def drop_nulls(
    glueContext, frame, nullStringSet, nullIntegerSet, transformation_ctx
) -> DynamicFrame:
    nullColumns = _find_null_fields(
        frame.glue_ctx, frame.schema(), "", [], nullStringSet, nullIntegerSet, frame
    )
    return DropFields.apply(
        frame=frame, paths=nullColumns, transformation_ctx=transformation_ctx
    )


def sparkSqlQuery(glueContext, query, mapping, transformation_ctx) -> DynamicFrame:
    for alias, frame in mapping.items():
        frame.toDF().createOrReplaceTempView(alias)
    result = spark.sql(query)
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)


args = getResolvedOptions(sys.argv, ["JOB_NAME", "input_file_path"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Default ruleset used by all target nodes with data quality enabled
DEFAULT_DATA_QUALITY_RULESET = """
    Rules = [
        ColumnCount > 0
    ]
"""

# Script generated for node Amazon S3
AmazonS3_node1764012789385 = glueContext.create_dynamic_frame.from_options(
    format_options={
        "quoteChar": '"',
        "withHeader": True,
        "separator": ",",
        "optimizePerformance": False,
    },
    connection_type="s3",
    format="csv",
    connection_options={"paths": [args["input_file_path"]], "recurse": True},
    transformation_ctx="AmazonS3_node1764012789385",
)

# Script generated for node Change Schema
ChangeSchema_node1764012987397 = ApplyMapping.apply(
    frame=AmazonS3_node1764012789385,
    mappings=[
        ("ticket_id", "string", "ticket_id", "string"),
        ("created_at", "string", "created_at", "timestamp"),
        ("resolved_at", "string", "resolved_at", "timestamp"),
        ("agent", "string", "agent", "string"),
        ("priority", "string", "priority", "string"),
        ("num_interactions", "string", "num_interactions", "int"),
        ("issuecat", "string", "issuecat", "string"),
        ("channel", "string", "channel", "string"),
        ("status", "string", "status", "string"),
        ("agent_feedback", "string", "agent_feedback", "string"),
    ],
    transformation_ctx="ChangeSchema_node1764012987397",
)

# Script generated for node Drop Null Fields
DropNullFields_node1764013128272 = drop_nulls(
    glueContext,
    frame=ChangeSchema_node1764012987397,
    nullStringSet={""},
    nullIntegerSet={},
    transformation_ctx="DropNullFields_node1764013128272",
)

# Script generated for node Rename Field- issuecat to issue_category
RenameFieldissuecattoissue_category_node1764013191739 = RenameField.apply(
    frame=DropNullFields_node1764013128272,
    old_name="issuecat",
    new_name="issue_category",
    transformation_ctx="RenameFieldissuecattoissue_category_node1764013191739",
)

# Script generated for node Filter-Select Interactions only positive
FilterSelectInteractionsonlypositive_node1764013273753 = Filter.apply(
    frame=RenameFieldissuecattoissue_category_node1764013191739,
    f=lambda row: (row["num_interactions"] >= 0),
    transformation_ctx="FilterSelectInteractionsonlypositive_node1764013273753",
)

# Script generated for node SQL Query-Fixed Priority Names
SqlQuery915 = """
select *,

case 
    when priority = 'Lw' THEN 'Low'
    when priority= 'Medum' THEN 'Medium'
    when priority="Hgh" THEN 'High'
ELSE priority
END AS priority

from myDataSource
"""
SQLQueryFixedPriorityNames_node1764013355797 = sparkSqlQuery(
    glueContext,
    query=SqlQuery915,
    mapping={"myDataSource": FilterSelectInteractionsonlypositive_node1764013273753},
    transformation_ctx="SQLQueryFixedPriorityNames_node1764013355797",
)

# Script generated for node Select Fields
SelectFields_node1764016059552 = SelectFields.apply(
    frame=SQLQueryFixedPriorityNames_node1764013355797,
    paths=[
        "ticket_id",
        "created_at",
        "resolved_at",
        "agent",
        "priority",
        "num_interactions",
        "issue_category",
        "channel",
        "status",
    ],
    transformation_ctx="SelectFields_node1764016059552",
)

# Script generated for node Amazon S3
EvaluateDataQuality().process_rows(
    frame=SelectFields_node1764016059552,
    ruleset=DEFAULT_DATA_QUALITY_RULESET,
    publishing_options={
        "dataQualityEvaluationContext": "EvaluateDataQuality_node1764012782355",
        "enableDataQualityResultsPublishing": True,
    },
    additional_options={
        "dataQualityResultsPublishing.strategy": "BEST_EFFORT",
        "observations.scope": "ALL",
    },
)
if SelectFields_node1764016059552.count() >= 1:
    SelectFields_node1764016059552 = SelectFields_node1764016059552.coalesce(1)
AmazonS3_node1764013796964 = glueContext.write_dynamic_frame.from_options(
    frame=SelectFields_node1764016059552,
    connection_type="s3",
    format="glueparquet",
    connection_options={
        "path": "s3://source-log-unstructured/support-tickets/processed/",
        "partitionKeys": [],
    },
    format_options={"compression": "snappy"},
    transformation_ctx="AmazonS3_node1764013796964",
)

job.commit()
