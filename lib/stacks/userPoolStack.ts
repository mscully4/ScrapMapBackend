import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { AccountRecovery, StringAttribute, UserPool, UserPoolClient } from 'aws-cdk-lib/aws-cognito';
import { AccountRootPrincipal, Effect, PolicyStatement, Role } from 'aws-cdk-lib/aws-iam';

export class UserPoolStack extends Stack {
  public userPool: UserPool;
  public userPoolClient: UserPoolClient;

  public userPoolRole: Role;

  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);

    this.userPool = new UserPool(this, 'travelMapUserPool', {
      accountRecovery: AccountRecovery.EMAIL_ONLY,
      standardAttributes: {
        email: {
          required: true,
          mutable: false
        },
      },
      customAttributes: {
        'name': new StringAttribute({ mutable: true }),
        'country': new StringAttribute({ mutable: true })
      },
      autoVerify: {
        email: true
      },
      passwordPolicy: {
        minLength: 8,
        requireDigits: false,
        requireSymbols: false
      },
      selfSignUpEnabled: true,
    })

    this.userPoolClient = new UserPoolClient(this, 'userPoolClient', {
      idTokenValidity: Duration.days(1),
      generateSecret: true,
      refreshTokenValidity: Duration.days(365),
      userPool: this.userPool,
      authFlows: {
        userPassword: true,
        adminUserPassword: true,
        userSrp: true,
      }
    })

    this.userPoolRole = new Role(this, 'userPoolAccessRole', {
      assumedBy: new AccountRootPrincipal()
    })

    const poolPolicyAddendum = new PolicyStatement({
      resources: [this.userPool.userPoolArn],
      effect: Effect.ALLOW,
      actions: [
        'cognito-idp:DescribeUserPoolClient',
        'cognito-idp:AdminInitiateAuth',
        'cognito-idp:InitiateAuth'
      ],
    });

    this.userPoolRole.addToPolicy(poolPolicyAddendum);
  }
}
