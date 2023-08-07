import argparse
import pandas as pd
import glob
import re
import numpy as np

def perturb_value(value, min, max, field):
    if min == 0 and max == 0:
        return 0
    perturbation = np.random.uniform(low=-0.1, high=0.1)
    return np.clip(value+perturbation, min_value[field], max_value[field])

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="Press Y to have data augmentation, anything else otherwise", default="n")
parser.add_argument("-o", "--output", help="Output csv file", required=True, default="output.csv")
args = parser.parse_args()
wantAugm = args.input
print("You chose the option with data aumentation." if wantAugm == 'Y' or wantAugm =='y'  else "You did not choose the data augmentation.")
pathRepoWithCsv = 'data\\input_data\\*.csv' # insert here the path to input csv(s)
input_files = glob.glob(pathRepoWithCsv)
problematic_columns = ['mdns', 'netbios', 'ssdp', 'dhcp']  # to edit with columns that contains string and not ints

# insert ip addr src and dst to check for the protocols needed to have a check
ipaddr = ['192.168.254.115', '10119224111']

# some protocols need to have same ip addr to the ones specified above
columns_to_check = ['rdp', 'icmp','tpkt']
# columns containing the ipaddresses
columns_with_ip = ['ipaddrsrc', 'ipaddrdst']
# boolean to set column labels to have the same ones of the csvs
setDf = True
id=0
for file in input_files:
    df = pd.read_csv(file)
    sizeDf = df.shape[0]
    columns = df.columns
    if(setDf):
        labels = df.columns[:-2].append(pd.Index(['output','length', 'noRdpTpkt', 'noRdpTpktIcmp', '_id']))
        df_output = pd.DataFrame(columns=labels)
        setDf = False

    # columns that contain strings must be converted to ints -> we want to count how many mdns packets there are
    # not taking into account the information inside, so we fill with -1
    for problematic_column in problematic_columns:
        df[problematic_column] = pd.to_numeric(df[problematic_column], errors='coerce').fillna(-1).astype(int)

    # compute the counts for every column
    counts = []
    for column in columns:
        if column in columns_with_ip:
            continue
        # filter rows that have ipaddr different to the ones in ipaddr array
        if column in columns_to_check:
            count = df.loc[(df[column] != 0) & (
                        (df[columns_with_ip[0]].apply(lambda x: str(x) in ipaddr)) | (
                    df[columns_with_ip[1]].apply(lambda x: str(x) in ipaddr))), column].count()
            if column=='icmp':
                count*=2        #since icmp echo reply tipe is 0, it wouldnt be detected as icmp, so we double it
        else:
            count = df.loc[df[column] != 0, column].count()
        counts.append(count/sizeDf*100)

    # add output label to the row (to edit if the filename does not contain number label)
    match = re.search(r'\d+', file)
    if match:
        label = int(match.group())
        # Add "label" column with the extracted valye
        counts.append((int(label)-1))
    counts.append(sizeDf)
    counts.append(1 if (counts[0] == 0 and counts[2] == 0) else 0)
    counts.append(1 if (counts[0] == 0 and counts[1] == 0 and counts[2] == 0) else 0)

    counts.append(int(id))
    id+=1
    df_output.loc[len(df_output)] = counts
outputCsv = args.output

if(not wantAugm == "Y" and not wantAugm == "y"):
    df_output.to_csv(outputCsv, index=False)
else:
    # data augmentation
    print("Starting perturbation!")
    df = pd.read_csv('output.csv')
    array = []
    for class_value in df['output'].unique():
        class_rows = df[df['output'] == class_value]
        # min_value = class_rows[['rdp', 'icmp','tpkt','mdns','arp','length']].min()
        min_value = class_rows[['rdp', 'netbios','smb','dhcp','ssdp','tpkt','mdns','arp','length']].min()

        # max_value = class_rows[['rdp', 'icmp','tpkt','mdns','arp','length']].max()
        max_value = class_rows[['rdp', 'netbios','smb','dhcp','ssdp','tpkt','mdns','arp','length']].max()

        # print(max_value)

        # Generazione delle righe con valori perturbati
        for _ in range(100):  # Numero di righe generate
            perturbed_values = {
                'output': class_value,
                'rdp': perturb_value(np.random.uniform(low=min_value['rdp'], high=max_value['rdp']), min_value['rdp'], max_value['rdp'], 'rdp'),
                # 'icmp': perturb_value(np.random.uniform(low=min_value['icmp'], high=max_value['icmp']), min_value['icmp'], max_value['icmp'],'icmp'),
                'tpkt': perturb_value(np.random.uniform(low=min_value['tpkt'], high=max_value['tpkt']), min_value['tpkt'], max_value['tpkt'],'tpkt'),
                'mdns': perturb_value(np.random.uniform(low=min_value['mdns'], high=max_value['mdns']), min_value['mdns'], max_value['mdns'],'mdns'),
                'arp': perturb_value(np.random.uniform(low=min_value['arp'], high=max_value['arp']), min_value['arp'], max_value['arp'],'arp'),
                'netbios': perturb_value(np.random.uniform(low=min_value['netbios'], high=max_value['netbios']), min_value['netbios'], max_value['netbios'], 'netbios'),
                'smb': perturb_value(np.random.uniform(low=min_value['smb'], high=max_value['smb']), min_value['smb'], max_value['smb'], 'smb'),
                'dhcp': perturb_value(np.random.uniform(low=min_value['dhcp'], high=max_value['dhcp']), min_value['dhcp'], max_value['dhcp'], 'dhcp'),
                'ssdp': perturb_value(np.random.uniform(low=min_value['ssdp'], high=max_value['ssdp']), min_value['ssdp'], max_value['ssdp'], 'ssdp'),
                'length': int(perturb_value(np.random.uniform(low=min_value['length'], high=max_value['length']), min_value['length'], max_value['length'],'length')),
                'noRdpTpkt': 0 if class_value == 0 else 1,
                'noRdpTpktIcmp': 0 if class_value == 0 or class_value == 1 else 1,
                '_id': id
            }
            id+=1
            array.append(perturbed_values)
    df_final = pd.concat([df_output,pd.DataFrame(array)])
    df_final.to_csv(outputCsv, index=False)

