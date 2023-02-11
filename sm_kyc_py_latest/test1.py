


#from modules.FDACOMPLETE import ItrAcknowledgementVerification

#if __name__ == '__main__':

    #v = ItrAcknowledgementVerification(pan_number="ALGPJ6855K", acknowledgement_number = '601513250310318',refid="testing2", env = 'quality')
    #data = v.ITR_response()
    #print(data)
from modules.Shop_AND_Establishment import Shopestablished

if __name__ == '__main__':

    v = Shopestablished(refid="testing2", env = 'prod')
    data = v.Shopestablished_response(licenseNumber = 'SEA/ADI/ALO/ID/30653/2017',state = 'Telangana')
    print(data)

#if __name__ == '__main__':

 #   v = Shop(refid="testing2", env = 'prod')
  #  data = v.Shop_response(shopEstablishmentName = 'Mayur Sweets and Bakers',state = 'Delhi', category = 'Shop', natureOfBusiness = 'Bakery & Confectioners')
   # print(data)

