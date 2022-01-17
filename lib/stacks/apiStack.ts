import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { CfnAuthorizer, AuthorizationType, RequestValidator, LambdaIntegration, ProxyResource, Resource, RestApi, Method, Model, JsonSchemaType } from 'aws-cdk-lib/aws-apigateway'
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

    const requestValidator = new RequestValidator(this, 'ApiRequestValidator', {
      restApi: this.restApi,
      validateRequestParameters: true,
      validateRequestBody: true
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

    // Destinations
    const destinationsApiResource = new Resource(this, 'destinationsApiResource', {
      pathPart: 'destinations',
      parent: this.restApi.root
    })

    const destinationsGetFunction = new Function(this, 'destinationsGetFunction', {
      runtime: Runtime.PYTHON_3_8,
      memorySize: 128,
      timeout: Duration.seconds(30),
      handler: "api.v1.destinations.get.lambda_handler",
      code: Code.fromAsset('src/'),
      environment: {
        PYTHONPATH: "/var/runtime:/opt",
        DYNAMO_READ_ROLE_ARN: props.dynamoTableReadRole.roleArn,
        DYNAMO_TABLE_NAME: props.dynamoTableName
      },
      layers: [flaskLayer]
    })

    if (destinationsGetFunction.role) {
      props.dynamoTableReadRole.grant(destinationsGetFunction.role, 'sts:AssumeRole')
    }

    destinationsApiResource.addMethod('GET', new LambdaIntegration(destinationsGetFunction), { 
      authorizationType: AuthorizationType.COGNITO,
      authorizer: {
        authorizerId: cognitoRequestAuthorizer.ref
      },
      requestValidator: requestValidator,
      requestParameters: {
        "method.request.querystring.user": true,
      }
    })

    const destinationsPostFunction = new Function(this, 'destinationsPostFunction', {
      runtime: Runtime.PYTHON_3_8,
      memorySize: 128,
      timeout: Duration.seconds(30),
      handler: "api.v1.destinations.post.lambda_handler",
      code: Code.fromAsset('src/'),
      environment: {
        PYTHONPATH: "/var/runtime:/opt",
        DYNAMO_WRITE_ROLE_ARN: props.dynamoTableWriteRole.roleArn,
        DYNAMO_TABLE_NAME: props.dynamoTableName
      },
      layers: [flaskLayer]
    })

    if (destinationsPostFunction.role) {
      props.dynamoTableWriteRole.grant(destinationsPostFunction.role, 'sts:AssumeRole')
    }

    const destinationsModel = new Model(this, "destinationsModel", {
      restApi: this.restApi,
      contentType: "application/json",
      modelName: "destinationsModel",
      schema: {
        type: JsonSchemaType.OBJECT,
        required: ["place_id", "name", "country", "country_code", "latitude", "longitude"],
        properties: {
          place_id: { type: JsonSchemaType.STRING },
          name: { type: JsonSchemaType.STRING },
          country: { type: JsonSchemaType.STRING },
          country_code: { type: JsonSchemaType.STRING },
          latitude: { type: JsonSchemaType.NUMBER },
          longitude: { type: JsonSchemaType.NUMBER },
        },
      },
    });

    destinationsApiResource.addMethod('POST', new LambdaIntegration(destinationsPostFunction), { 
      authorizationType: AuthorizationType.COGNITO,
      authorizer: {
        authorizerId: cognitoRequestAuthorizer.ref
      },
      requestValidator: requestValidator,
      requestModels: {
        "application/json": destinationsModel
      }
    })

    const destinationsDeleteFunction = new Function(this, 'destinationsDeleteFunction', {
      runtime: Runtime.PYTHON_3_8,
      memorySize: 128,
      timeout: Duration.seconds(30),
      handler: "api.v1.destinations.delete.lambda_handler",
      code: Code.fromAsset('src/'),
      environment: {
        PYTHONPATH: "/var/runtime:/opt",
        DYNAMO_WRITE_ROLE_ARN: props.dynamoTableWriteRole.roleArn,
        DYNAMO_TABLE_NAME: props.dynamoTableName
      },
      layers: [flaskLayer]
    })

    if (destinationsDeleteFunction.role) {
      props.dynamoTableWriteRole.grant(destinationsDeleteFunction.role, 'sts:AssumeRole')
    }

    destinationsApiResource.addMethod('DELETE', new LambdaIntegration(destinationsDeleteFunction), { 
      authorizationType: AuthorizationType.COGNITO,
      authorizer: {
        authorizerId: cognitoRequestAuthorizer.ref
      },
      requestValidator: requestValidator,
      requestParameters: {
        "method.request.querystring.place_id": true,
      }
    });

  }
}
