import pandas as pd
import vowpalwabbit
import numpy as np
import uuid
import snowflake.connector

def bandit_data_set_grundstruktur(bandit_dataset, placeID):
    bandit_dataset['CorrelationId'] = [uuid.uuid4() for _ in range(len(bandit_dataset))]
    bandit_dataset['original_placeID'] = bandit_dataset[placeID]
    bandit_dataset['Action'] =bandit_dataset[placeID] 
    bandit_dataset['Action_nr'] =bandit_dataset[placeID] 
    bandit_dataset['prob_action'] = np.random.rand(len(bandit_dataset))
    # Create a new dataframe with unique placeIDs and assign new IDs
    new_id_df = pd.DataFrame({placeID: bandit_dataset[placeID].unique(),
                            'new_ID': range(1, 113)})
    # Merge the two dataframes together based on "placeID"
    merged_df = pd.merge(bandit_dataset, new_id_df, on=placeID)
    bandit_dataset = merged_df
    bandit_dataset['Action'] = bandit_dataset['new_ID']
    return bandit_dataset

def get_place_id_Mapping(bandit_dataset, placeID):
    bandit_dataset['CorrelationId'] = [uuid.uuid4() for _ in range(len(bandit_dataset))]
    bandit_dataset['original_placeID'] = bandit_dataset[placeID]

    return bandit_dataset
def placeIDgeben(data, PLACEID, Nummer):
    bandit_data = bandit_data_set_grundstruktur(data, PLACEID)
    bandit_ = bandit_data[['Action', 'PLACEID']]
    bandit_= bandit_[bandit_['Action'] == Nummer]
    return bandit_['PLACEID'].iloc[0]


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    

def create_shared_user_feature_string_list(user_feature_dict):
    feature_list = []
    for k, v in user_feature_dict.items():
        if is_number(v):
            feature_list.append(f"{k}:{v}")
        else:
            feature_list.append(f"{k}_{v}")
    return [f"{' '.join(feature_list)}"]


import snowflake.connector


def create_snowflake_connection():
    conn = snowflake.connector.connect(
        account="ihidwgg-anb43019",
        password="Roberto_Vitor_2023!",
        user="AJKSLD",
        warehouse="compute_wh",
        database="BANDIT",
        schema="DATA"
    )

    return conn



def get_place_data(place_id):
    conn = create_snowflake_connection()

    try:
        query = f"""
        SELECT PLACEID, NAME, ADVERTISMENT, IMAGE_URL
        FROM restaurants
        WHERE PLACEID = %s;
        """

        cur = conn.cursor()
        cur.execute(query, (place_id,))
        result = cur.fetchall()
        columns = ['PlaceID', 'Name', 'Advertisment', 'Image_url']
        df = pd.DataFrame(result, columns=columns)
        return df

    finally:
        conn.close()


def formatting_and_training_bandit_input_data(bandit, vowpal_workspace, filename):
    for i in bandit.CorrelationId.unique():
        bandit_loop = bandit[bandit['CorrelationId'] == i]
        context = bandit_loop[['VALIDATED_PARKING',  'MON_TUE_WED_THU_FRI', 'SAT', 'SUN','YES', 'BAKERY', 'BAR', 'BAR_PUB_BREWERY', 'BARBECUE', 'BREAKFAST_BRUNCH', 'MEXICAN', 'VEGETARIAN', 'INTERNATIONAL', ]].iloc[:1]
        context_dict = context.to_dict('r')
        bandit_loop.reset_index(inplace=True, drop=True)
        action = bandit_loop.Action
        prob_action = bandit_loop.prob_action
        reward = bandit_loop.RATING * -1
        daten =[
        create_shared_user_feature_string_list(context_dict[0])[0],
            

        ]
        daten = f"{bandit_loop.Action.iloc[0 ]}:{reward.iloc[0]}:{prob_action.iloc[0 ]} | {str(daten[0])[1:-1]}" 

        vowpal_workspace.learn(daten)
    vowpal_workspace.save(f"cb.{filename}")
    vowpal_workspace.finish()
    return print(daten)



def formatting_and_predicting_bandit_input_data(bandit, vowpal_workspace):
    prediction_result = []
    predicted_rewards_all_actions = []
    UserIds = []
    pred_nl_slot = []
    for i in bandit.CorrelationId.unique():
        bandit_loop = bandit[bandit['CorrelationId'] == i]
        context = bandit_loop[['VALIDATED_PARKING',  'MON_TUE_WED_THU_FRI', 'SAT', 'SUN', 'YES', 'BAKERY', 'BAR', 'BAR_PUB_BREWERY', 'BARBECUE', 'BREAKFAST_BRUNCH', 'MEXICAN', 'VEGETARIAN', 'INTERNATIONAL', ]].iloc[:1]
        context_dict = context.to_dict('r')
        bandit_loop.reset_index(inplace=True, drop=True)
        # action = bandit_loop.Action
        # prob_action = bandit_loop.prob_action
        # reward = bandit_loop.RATING * -1
        daten =[
        create_shared_user_feature_string_list(context_dict[0])[0],
            

        ]
        
        #daten = f"{bandit_loop.Action.iloc[0 ]}:{reward.iloc[0]}:{prob_action.iloc[0 ]} | {str(daten[0])[1:-1]}" 
        daten = f" | {str(daten[0])[1:-1]}" 
        pred= vowpal_workspace.predict(daten)
       
        prediction_result.append(pred)
    returned_df =pd.DataFrame({'predicted_actionID': prediction_result,  }, columns=['predicted_actionID',  ])
    return returned_df





