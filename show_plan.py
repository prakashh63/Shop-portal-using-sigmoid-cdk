"""After `cdk synth`: read cdk.out and show how the architecture was built. No AWS needed."""

import json
from pathlib import Path

template = json.loads((Path(__file__).parent / "cdk.out" / "ShopPortalStack.template.json").read_text())
items = template["Resources"]


def of(resource_type):
    return [r["Properties"] for r in items.values() if r["Type"] == resource_type]


print("== S3 buckets (all private) ==")
for b in of("AWS::S3::Bucket"):
    pab = b["PublicAccessBlockConfiguration"]
    print(f"  {b['BucketName']}: public access blocked = {all(pab.values())}")

print("== CloudFront (single HTTPS entry point) ==")
cfg = of("AWS::CloudFront::Distribution")[0]["DistributionConfig"]
print(f"  /          -> {cfg['DefaultCacheBehavior']['ViewerProtocolPolicy']}")
for behavior in cfg["CacheBehaviors"]:
    print(f"  {behavior['PathPattern']:<10} -> {behavior['ViewerProtocolPolicy']}")
print(f"  origin access controls (OAC): {len(of('AWS::CloudFront::OriginAccessControl'))}")

print("== API Gateway ==")
settings = of("AWS::ApiGateway::Stage")[0]["MethodSettings"][0]
print(f"  throttling rate={settings['ThrottlingRateLimit']} burst={settings['ThrottlingBurstLimit']}")
print("  path parts:", sorted(r["PathPart"] for r in of("AWS::ApiGateway::Resource")))

print("== Lambdas ==")
for fn in of("AWS::Lambda::Function"):
    variables = fn.get("Environment", {}).get("Variables", {})
    buckets = [name for name in variables if name.startswith("BUCKET_")]
    print(f"  {fn['FunctionName']:<18} runtime={fn['Runtime']:<10} bucket env vars={buckets or '-'}")

print("== S3 permissions per Lambda role (explicit actions, no wildcards) ==")
for logical_id, resource in items.items():
    if resource["Type"] != "AWS::IAM::Policy":
        continue
    actions = set()
    for statement in resource["Properties"]["PolicyDocument"]["Statement"]:
        action = statement["Action"]
        actions.update(action if isinstance(action, list) else [action])
    s3_actions = sorted(a for a in actions if a.startswith("s3:"))
    if s3_actions:
        print(f"  {logical_id[:40]:<40} {s3_actions}")

print("== Triggers ==")
for topic in of("AWS::SNS::Topic"):
    print(f"  SNS topic {topic['TopicName']} (encrypted: {'KmsMasterKeyId' in topic})")
print(f"  SNS subscriptions: {len(of('AWS::SNS::Subscription'))}")
for rule in of("AWS::Events::Rule"):
    print(f"  EventBridge schedule: {rule.get('ScheduleExpression')}")

print("== Logging and encryption ==")
print(f"  log groups={len(of('AWS::Logs::LogGroup'))}, kms keys={len(of('AWS::KMS::Key'))}, "
      f"roles={len(of('AWS::IAM::Role'))}")
