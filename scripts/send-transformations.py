#!/usr/bin/env python3

import argparse, sys, os
import yaml
import subprocess
import pprint
import logging


# ---------------------
def get_config():
    """ Parse configuration options for script. 
        To avoid bootstrap problems there are no defaults.

    """

    parser = argparse.ArgumentParser(
      description="Run Google calendar helper scripts and send "
        "the output somewhere (publish feeds, mail newsletters, etc)",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter,
      )

    parser.add_argument('-c', '--configfile',
      help='YAML config file location',
      required=True,
      )
    parser.add_argument('-t', '--transforms',
      help='The transformations to run',
      required=True,
      choices=['rss','newsletter','sidebar','tweets'],
      nargs='+'
      )

    args = parser.parse_args()

    # Config location is required, so we must get here!
    config_location = os.path.abspath(args.configfile)
    #print("config file: {}".format(config_location))

    #print("{}".format(args))

    config = None

    with open(config_location, encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    if config:
        config['transform_targets'] = args.transforms

    return config
    
# ---------------------------------
def assemble_email(to_address, from_address, subject, body_string):
    """ Construct an email the hard way 
    """

    retval = ""
    retval += "To: {}\n".format(to_address)
    retval += "From: {}\n".format(from_address)
    retval += "Subject: {}\n".format(subject)
    retval += 'Content-Type: text/plain; charset="UTF-8"\n'
    
    # Forget requiring pytz. Just call shell functions. 
    email_date = subprocess.check_output(['date', '-R']).decode()


    retval += "Date: {}\n\n".format(email_date)


    retval += body_string
    retval += "\n"

    return retval

# ---------------------------------
def send_mail(text, to_addr, account):
    """ Send the email using msmtp. account is the account in .msmtprc
    """

    # check_call does not take input in Python 3.4. 
    # But check_output does??

    dummy = subprocess.check_output(
      ['msmtp', '-a', account, to_addr],
      input=text.encode()
      )

# ----------------------------------
def get_subject(conf, operation):
  
    subject_date = subprocess.check_output(
      ['date', '+%b %d, %Y']
      ).decode().rstrip()

    subject = "INVALID"

    if 'subject_prefix' in conf[operation]:
        subject =  "{} ({} listing)".format(
          conf[operation]['subject_prefix'],
          subject_date,
          )
    
    else:
        subject = "Events listing ({})".format(
          subject_date
          )

    return subject


# ---------------------------------
def run_transforms():
    full_config = get_config()

    # Activate the environment 
    activate_this_file = os.path.join(
      full_config['venvdir'],
      'bin',
      'activate_this.py'
      )
    # https://stackoverflow.com/questions/6943208/
    exec(
      compile(
        open(activate_this_file, "rb").read(),
        activate_this_file, 
        'exec',
        ), 
      dict(__file__=activate_this_file)
      )

    log = open(full_config['logfile'], 'a', encoding='utf-8')
    logging.basicConfig(
      filename=full_config['logfile'], 
      level=logging.INFO,
      format='%(asctime)s %(filename)s: %(message)s',
      )


    for operation in full_config['transform_targets']:
        for target in full_config['targets']:

            #pprint.pprint(full_config['targets'][conf]['transforms'])

            conf = full_config['targets'][target]

            if operation in conf['transforms']:
                logging.info("Performing operation {} on target {}".format(
                  operation,
                  target,
                  ))


                script_name = None

                if operation == 'newsletter':
                    script_name = 'gen_newsletter.py'
                elif operation == 'sidebar':
                    script_name = 'gen_sidebar.py'
                elif operation == 'rss':
                    script_name = 'gen_rss.py'
                elif operation == 'tweets':
                    script_name = 'schedule_event_tweets.py'

                call_succeeded = False

                try:
                    subprocess.check_call(
                      [os.path.join(full_config['pydir'], script_name),
                        '--configfile',
                        os.path.join(
                          full_config['confdir'],
                          conf['configfile'],
                          ),
                       ],
                       stdout=log,
                       stderr=log,
                       )
                    call_succeeded = True

                # If the call fails, send an alert
                except subprocess.CalledProcessError as e:
                    body = ("Call to {} for target {} "
                      "failed with error code {} .").format(
                        e.cmd,
                        target,
                        e.returncode,
                        )
                    email = assemble_email(
                      full_config['admin_email'],
                      conf['from_address'],
                      "Operation {} failed for {}".format(
                        script_name,
                        target,
                        ),
                      body
                      )
                    send_mail(
                      email,
                      full_config['admin_email'],
                      conf['msmtp_account'],
                      )



                # Only certain operations have email 
                if call_succeeded and operation in ['newsletter', 'sidebar']: 
                    subject = get_subject(conf, operation)
                    logging.debug("Subject is '{}'".format(subject))

                    body = None

                    resultfile = os.path.join(
                      full_config['outputdir'],
                      conf[operation]['body']
                      )

                    with open(resultfile, encoding='utf-8') as f:
                        body = f.read()

                    email = assemble_email(
                      conf[operation]['to_address'], 
                      conf['from_address'], 
                      subject, 
                      body
                      )

                    send_mail(
                      email,
                      conf[operation]['to_address'],
                      conf['msmtp_account'],
                      )
                    

                # If the subprocess failed then send admin an email

    #pprint.pprint(full_config)




# MAIN PROGRAM 

run_transforms()
