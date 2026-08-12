from app.rules.rule import DetectionRule, RuleCondition


AWS_RULES = [
    # =========================================================
    # AUTHENTICATION RULES
    # =========================================================

    DetectionRule(
        rule_id="AWS-AUTH-001",
        name="Successful Console Login Without MFA",
        description=(
            "Detects successful AWS console login "
            "performed without MFA."
        ),
        severity="high",
        cloud_provider="aws",
        service="signin",
        event_name="ConsoleLogin",
        conditions=[
            RuleCondition(
                field="raw_event.additionalEventData.MFAUsed",
                operator="equals",
                value="No",
            ),
            RuleCondition(
                field="raw_event.responseElements.ConsoleLogin",
                operator="equals",
                value="Success",
            ),
        ],
        mitre_tactic="Initial Access",
        mitre_technique="Valid Accounts",
        mitre_technique_id="T1078",
    ),

    DetectionRule(
        rule_id="AWS-AUTH-002",
        name="Failed Console Login",
        description=(
            "Detects failed AWS Management Console "
            "login attempts."
        ),
        severity="medium",
        cloud_provider="aws",
        service="signin",
        event_name="ConsoleLogin",
        conditions=[
            RuleCondition(
                field="raw_event.responseElements.ConsoleLogin",
                operator="equals",
                value="Failure",
            ),
        ],
        mitre_tactic="Credential Access",
        mitre_technique="Brute Force",
        mitre_technique_id="T1110",
    ),

    DetectionRule(
        rule_id="AWS-AUTH-003",
        name="Failed Console Login Without MFA",
        description=(
            "Detects failed AWS console login attempts "
            "where MFA was not used."
        ),
        severity="high",
        cloud_provider="aws",
        service="signin",
        event_name="ConsoleLogin",
        conditions=[
            RuleCondition(
                field="raw_event.responseElements.ConsoleLogin",
                operator="equals",
                value="Failure",
            ),
            RuleCondition(
                field="raw_event.additionalEventData.MFAUsed",
                operator="equals",
                value="No",
            ),
        ],
        mitre_tactic="Credential Access",
        mitre_technique="Brute Force",
        mitre_technique_id="T1110",
    ),

    # =========================================================
    # ROOT ACCOUNT RULES
    # =========================================================

    DetectionRule(
        rule_id="AWS-ROOT-001",
        name="Root Account Console Login",
        description=(
            "Detects AWS Management Console login "
            "performed using the root account."
        ),
        severity="critical",
        cloud_provider="aws",
        service="signin",
        event_name="ConsoleLogin",
        conditions=[
            RuleCondition(
                field="raw_event.userIdentity.type",
                operator="equals",
                value="Root",
            ),
        ],
        mitre_tactic="Initial Access",
        mitre_technique="Valid Accounts",
        mitre_technique_id="T1078",
    ),

    DetectionRule(
        rule_id="AWS-ROOT-002",
        name="Root Account Sensitive IAM Activity",
        description=(
            "Detects sensitive IAM changes performed "
            "using the AWS root account."
        ),
        severity="critical",
        cloud_provider="aws",
        service="iam",
        conditions=[
            RuleCondition(
                field="raw_event.userIdentity.type",
                operator="equals",
                value="Root",
            ),
            RuleCondition(
                field="event_name",
                operator="in",
                value=[
                    "CreateUser",
                    "DeleteUser",
                    "CreateAccessKey",
                    "DeleteAccessKey",
                    "AttachUserPolicy",
                    "DetachUserPolicy",
                    "PutUserPolicy",
                    "DeleteUserPolicy",
                    "CreateLoginProfile",
                    "UpdateLoginProfile",
                    "DeleteLoginProfile",
                    "CreatePolicy",
                    "DeletePolicy",
                    "CreatePolicyVersion",
                    "SetDefaultPolicyVersion",
                ],
            ),
        ],
        mitre_tactic="Privilege Escalation",
        mitre_technique="Account Manipulation",
        mitre_technique_id="T1098",
    ),

    DetectionRule(
        rule_id="AWS-ROOT-003",
        name="Root Account CloudTrail Tampering",
        description=(
            "Detects CloudTrail modification or logging "
            "disruption performed using the root account."
        ),
        severity="critical",
        cloud_provider="aws",
        service="cloudtrail",
        conditions=[
            RuleCondition(
                field="raw_event.userIdentity.type",
                operator="equals",
                value="Root",
            ),
            RuleCondition(
                field="event_name",
                operator="in",
                value=[
                    "StopLogging",
                    "DeleteTrail",
                    "UpdateTrail",
                    "PutEventSelectors",
                ],
            ),
        ],
        mitre_tactic="Defense Evasion",
        mitre_technique="Impair Defenses",
        mitre_technique_id="T1562.001",
    ),

    DetectionRule(
        rule_id="AWS-ROOT-004",
        name="Root Account API Activity",
        description=(
            "Detects general API activity performed "
            "using the AWS root account."
        ),
        severity="medium",
        cloud_provider="aws",
        enabled=False,
        conditions=[
            RuleCondition(
                field="raw_event.userIdentity.type",
                operator="equals",
                value="Root",
            ),
        ],
    ),

    # =========================================================
    # IAM RULES
    # =========================================================

    DetectionRule(
        rule_id="AWS-IAM-001",
        name="IAM User Created",
        description="Detects creation of a new IAM user.",
        severity="medium",
        cloud_provider="aws",
        service="iam",
        event_name="CreateUser",
        mitre_tactic="Persistence",
        mitre_technique="Create Account",
        mitre_technique_id="T1136",
    ),

    DetectionRule(
        rule_id="AWS-IAM-002",
        name="IAM Access Key Created",
        description="Detects creation of a new IAM access key.",
        severity="medium",
        cloud_provider="aws",
        service="iam",
        event_name="CreateAccessKey",
        mitre_tactic="Persistence",
        mitre_technique="Account Manipulation",
        mitre_technique_id="T1098",
    ),

    # =========================================================
    # CLOUDTRAIL RULES
    # =========================================================

    DetectionRule(
        rule_id="AWS-TRAIL-001",
        name="CloudTrail Logging Stopped",
        description=(
            "Detects attempts to stop AWS CloudTrail logging."
        ),
        severity="critical",
        cloud_provider="aws",
        service="cloudtrail",
        event_name="StopLogging",
        mitre_tactic="Defense Evasion",
        mitre_technique="Impair Defenses",
        mitre_technique_id="T1562.001",
    ),

    DetectionRule(
        rule_id="AWS-TRAIL-002",
        name="CloudTrail Deleted",
        description=(
            "Detects deletion of an AWS CloudTrail trail."
        ),
        severity="critical",
        cloud_provider="aws",
        service="cloudtrail",
        event_name="DeleteTrail",
        mitre_tactic="Defense Evasion",
        mitre_technique="Impair Defenses",
        mitre_technique_id="T1562.001",
    ),

    # =========================================================
    # EC2 / NETWORK RULES
    # =========================================================

    DetectionRule(
        rule_id="AWS-EC2-001",
        name="Security Group Opened to Internet",
        description=(
            "Detects ingress rules allowing access "
            "from 0.0.0.0/0."
        ),
        severity="high",
        cloud_provider="aws",
        service="ec2",
        event_name="AuthorizeSecurityGroupIngress",
        conditions=[
            RuleCondition(
                field="raw_event.requestParameters.ipPermissions",
                operator="contains",
                value="0.0.0.0/0",
            ),
        ],
        mitre_tactic="Initial Access",
        mitre_technique="External Remote Services",
        mitre_technique_id="T1133",
    ),
]
