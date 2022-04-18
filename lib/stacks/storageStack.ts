import { Table, AttributeType, BillingMode } from 'aws-cdk-lib/aws-dynamodb';
import { Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { AccountRootPrincipal, Role } from 'aws-cdk-lib/aws-iam'

export class StorageStack extends Stack {
  public dynamoTableReadRole: Role;
  public dynamoTableWriteRole: Role;
  public dynamoTableName: string;

  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);

    const dynamoTable = new Table(this, `travelMapTable`, {
      partitionKey: {name: "PK", type: AttributeType.STRING},
      sortKey: {name: "SK", type: AttributeType.STRING},
      billingMode: BillingMode.PAY_PER_REQUEST
    })

    this.dynamoTableName = dynamoTable.tableName;

    this.dynamoTableReadRole = new Role(this, 'dynamoDBReadRole', {
      assumedBy: new AccountRootPrincipal()
    })

    this.dynamoTableWriteRole = new Role(this, 'dynamoDBWriteRole', {
      assumedBy: new AccountRootPrincipal()
    })

    dynamoTable.grantReadData(this.dynamoTableReadRole);
    dynamoTable.grantWriteData(this.dynamoTableWriteRole);

  }
}
