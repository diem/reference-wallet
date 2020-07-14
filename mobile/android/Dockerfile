FROM circleci/android:api-28-node


RUN gem install fastlane -NV
RUN sdkmanager --install \
          "ndk;21.2.6472646" \
          "cmake;3.10.2.4988404"
