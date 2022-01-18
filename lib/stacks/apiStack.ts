import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { CfnAuthorizer, AuthorizationType, LambdaIntegration, ProxyResource, Resource, RestApi } from 'aws-cdk-lib/aws-apigateway'
import { Code, Function, Runtime, LayerVersion } from 'aws-cdk-lib/aws-lambda';
import { Role } from 'aws-cdk-lib/aws-iam';
import { UserPool } from 'aws-cdk-lib/aws-cognito';

interface apiStackProps extends StackProps {
  userPool: UserPool,
  clientId: string,
  userPoolRole: Role,
  dynamoTableReadRole: Role,
  dynamoTableWriteRole: Role,
  dynamoTableName: string,
}

export class ApiStack extends Stack {
  public restApi: RestApi;

  constructor(scope: Construct, id: string, props: apiStackProps) {
    super(scope, id, props);

    this.restApi = new RestApi(this, 'scrapMapRestApi', {})

    //Utilities
    const cognitoRequestAuthorizer = new CfnAuthorizer(this, "cognitoRequestAuthorizer", {
      name: "cognitoRequestAuthorizer",
      identitySource: "method.request.header.Authorization",
      restApiId: this.restApi.restApiId,
      type: AuthorizationType.COGNITO,
      providerArns: [props.userPool.userPoolArn]
    })

    const authApiResource = new Resource(this, 'authApiResource', {
      pathPart: 'auth',
      parent: this.restApi.root
    })

    const flaskLayer = new LayerVersion(this, 'flaskLambdaLayer', {
      compatibleRuntimes: [
        Runtime.PYTHON_3_9,
        Runtime.PYTHON_3_8,
      ],
      code: Code.fromAsset('layers/flask'),
    });

    const authProxyFunction = new Function(this, 'authProxyFunction', {
      runtime: Runtime.PYTHON_3_8,
      memorySize: 128,
      timeout: Duration.seconds(30),
      handler: "api.v1.auth.lambda_function.lambda_handler",
      code: Code.fromAsset('src/'),
      environment: {
        PYTHONPATH: "/var/runtime:/opt",
        USER_POOL_ID: props.userPool.userPoolId,
        CLIENT_ID: props.clientId,
        USER_POOL_ACCESS_ROLE_ARN: props.userPoolRole.roleArn
      },
      layers: [flaskLayer]
    })

    if (authProxyFunction.role) {
      props.userPoolRole.grant(authProxyFunction.role, 'sts:AssumeRole')
    }

    const authProxyResource = new ProxyResource(this, 'authApiProxyResource', {
      parent: authApiResource,
      anyMethod: true,
      defaultIntegration: new LambdaIntegration(authProxyFunction),
    })
  }
}
